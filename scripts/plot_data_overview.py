"""Read frozen manifests/YOLO labels and draw reproducible dataset overview figures."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZipFile

CLASSES={0:'fire',1:'smoke'}
RECORDS=(('public_optical_release_v1','public optical','public-optical-v1'),
         ('paired_rgbt_v1','paired_RGBT','paired-rgbt-v1'))


def file_sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        yield from csv.DictReader(f)


def write_csv(path, fields, records):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        w.writeheader()
        w.writerows(records)


def parse_yolo(raw):
    result=[]
    for number,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
        if not line.strip():
            continue
        fields=line.split()
        if len(fields)!=5:
            raise ValueError(f'YOLO row {number} does not have five fields')
        values=[float(value) for value in fields]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Non-finite annotation coordinate')
        cls=values[0]
        if cls not in CLASSES or cls!=int(cls):
            raise ValueError('Unknown annotation class')
        x,y,w,h=values[1:]
        if w<=0 or h<=0:
            raise ValueError('Non-positive box size; no annotation is silently discarded')
        result.append((int(cls),x,y,w,h))
    return result


class FrozenReader:
    def __init__(self,stack,data_root,directory,catalog_dir,archive_dirs,verify_archives):
        self.base=Path(data_root)/directory
        self.directory=directory
        self.index={}
        self.parts=[]
        self.dimension_audit=[]
        if catalog_dir:
            prefix=next(p for _,d,p in RECORDS if d==directory)
            catalog=read_json(Path(catalog_dir)/(prefix+'-archives.json'))
            if catalog['directory']!=directory:
                raise ValueError('Archive catalog root mismatch')
            for part in catalog['parts']:
                candidates=[Path(d)/part['name'] for d in archive_dirs if (Path(d)/part['name']).is_file()]
                if len(candidates)!=1:
                    raise ValueError('Archive part missing or ambiguous: '+part['name'])
                path=candidates[0]
                if path.stat().st_size!=part['bytes']:
                    raise ValueError('Archive size differs')
                if verify_archives and file_sha256(path)!=part['sha256']:
                    raise ValueError('Archive hash differs')
                archive=stack.enter_context(ZipFile(path))
                for info in archive.infolist():
                    if info.filename in self.index:
                        raise ValueError('Duplicate archive member')
                    if not info.filename.startswith(directory+'/'):
                        raise ValueError('Archive member has wrong root')
                    self.index[info.filename]=(archive,info)
                self.parts.append({'name':part['name'],'sha256':part['sha256'],'hash_checked_now':verify_archives})

    def open(self,relative):
        if '\\' in relative or relative.startswith('/') or any(v in ('','..','.') for v in relative.split('/')):
            raise ValueError('Unsafe relative payload path')
        if self.index:
            archive,info=self.index[self.directory+'/'+relative]
            return archive.open(info)
        path=self.base.joinpath(*relative.split('/'))
        if not path.resolve().is_relative_to(self.base.resolve()) or path.is_symlink():
            raise ValueError('Payload path escapes record')
        return path.open('rb')

    def label(self,relative,expected):
        with self.open(relative) as f:
            raw=f.read()
        if len(expected)!=64 or hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError('Frozen label SHA-256 differs: '+relative)
        return raw,parse_yolo(raw)

    def dimensions(self,relative,expected):
        from PIL import Image
        with self.open(relative) as f, Image.open(f) as image:
            encoded=image.size
            orientation=image.getexif().get(274,1)
        actual=encoded[::-1] if orientation in (5,6,7,8) else encoded
        if encoded!=actual or tuple(expected)!=actual:
            self.dimension_audit.append({'directory':self.directory,'image_path':relative,
                'manifest_width':expected[0],'manifest_height':expected[1],
                'encoded_width':encoded[0],'encoded_height':encoded[1],
                'exif_orientation':orientation,'oriented_width':actual[0],'oriented_height':actual[1],
                'manifest_matches_oriented':tuple(expected)==actual})
        return actual


def collect(repo,output,catalog_dir=None,archive_dirs=(),verify_archives=True,verify_images=False):
    import numpy as np
    output=Path(output)
    protected=[Path(repo)/directory for _,directory,_ in RECORDS]+[Path(repo)/'metadata']
    if any(output.resolve().is_relative_to(p.resolve()) for p in protected):
        raise ValueError('Figure output must not be written into protected dataset/metadata directories')
    (output/'statistics').mkdir(parents=True,exist_ok=True)
    (output/'private').mkdir(exist_ok=True)
    sizes=Counter()
    samples=Counter()
    geometry=defaultdict(list)
    outside=Counter()
    negative=Counter()
    dimension_audit=[]
    verification={'label_files_sha256_checked':0,'retained_image_headers_checked':0,'manifests':{},'archive_parts':[]}

    def add_boxes(group,parsed,width,height):
        for cls,x,y,w,h in parsed:
            geometry[(group,CLASSES[cls])].append((w,h,w*h,w*width,h*height,w*h*width*height))
            if min(x-w/2,y-h/2)<-1e-6 or max(x+w/2,y+h/2)>1+1e-6:
                outside[(group,CLASSES[cls])]+=1

    for identifier,directory,_ in RECORDS:
        manifest=Path(repo)/directory/'metadata/manifest.csv'
        verification['manifests'][identifier]=file_sha256(manifest)
        with ExitStack() as stack:
            reader=FrozenReader(stack,repo,directory,catalog_dir,archive_dirs,verify_archives)
            verification['archive_parts'].extend(reader.parts)
            for row in rows(manifest):
                if identifier==RECORDS[0][0]:
                    width,height=int(row['width']),int(row['height'])
                    samples[('public_optical',row['source_dataset'],row['split'])]+=1
                    if verify_images:
                        width,height=reader.dimensions(row['image_path'],(width,height))
                        verification['retained_image_headers_checked']+=1
                    sizes[('public_optical','all','optic',width,height)]+=1
                    _,boxes=reader.label(row['label_path'],row['label_sha256'])
                    verification['label_files_sha256_checked']+=1
                    if len(boxes)!=int(row['box_count']):
                        raise ValueError('Public annotation count differs from manifest')
                    add_boxes('public_optical',boxes,width,height)
                    negative['public_optical']+=not boxes
                else:
                    width,height=int(row['optic_width']),int(row['optic_height'])
                    tw,th=int(row['thermal_width']),int(row['thermal_height'])
                    domain=row['domain']
                    samples[('paired_rgbt',domain,row['split'])]+=1
                    if verify_images:
                        width,height=reader.dimensions(row['optic_path'],(width,height))
                        tw,th=reader.dimensions(row['thermal_path'],(tw,th))
                        verification['retained_image_headers_checked']+=2
                    sizes[('paired_rgbt',domain,'optic',width,height)]+=1
                    sizes[('paired_rgbt',domain,'thermal',tw,th)]+=1
                    _,source=reader.label(row['source_label_path'],row['source_label_sha256'])
                    optic_raw,canonical=reader.label(row['training_optic_label_path'],row['training_label_sha256'])
                    thermal_raw,_=reader.label(row['training_thermal_label_path'],row['training_label_sha256'])
                    verification['label_files_sha256_checked']+=3
                    if optic_raw!=thermal_raw:
                        raise ValueError('Paired common canonical modality labels differ')
                    counts=Counter(CLASSES[b[0]] for b in source)
                    if any(counts[c]!=int(row['source_'+c+'_boxes']) for c in CLASSES.values()):
                        raise ValueError('Paired source class count differs from manifest')
                    add_boxes('paired_source',source,width,height)
                    add_boxes('paired_canonical',canonical,width,height)
                    add_boxes('paired_canonical_'+domain,canonical,width,height)
                    negative['paired_canonical']+=not canonical
            dimension_audit.extend(reader.dimension_audit)
            print(json.dumps({'stage':'record_scanned','dataset':identifier,'checked_labels':verification['label_files_sha256_checked'],
                              'checked_image_headers':verification['retained_image_headers_checked']}),flush=True)
    arrays={group+'__'+cls:np.asarray(values,dtype=np.float64) for (group,cls),values in geometry.items()}
    np.savez_compressed(output/'private/box_geometry.npz',**arrays)
    write_csv(output/'statistics/sample_counts.csv',['dataset','component','split','samples','unit'],[
        dict(dataset=d,component=c,split=s,samples=n,unit='images' if d=='public_optical' else 'pairs')
        for (d,c,s),n in sorted(samples.items())])
    write_csv(output/'statistics/image_resolutions.csv',['dataset','domain','modality','width','height','images'],[
        dict(dataset=d,domain=domain,modality=m,width=w,height=h,images=n)
        for (d,domain,m,w,h),n in sorted(sizes.items())])
    metrics={}
    summary_rows=[]
    for key,a in arrays.items():
        group,cls=key.split('__')
        record={'boxes':len(a),'out_of_frame_boxes':outside[(group,cls)]}
        for i,name in enumerate(('relative_width','relative_height','relative_area','pixel_width','pixel_height','pixel_area')):
            q=np.percentile(a[:,i],[0,5,25,50,75,95,100])
            record[name]=dict(zip(('min','p05','p25','median','p75','p95','max'),map(float,q)))
        metrics[key]=record
        summary_rows.append({'group':group,'class':cls,'boxes':len(a),'out_of_frame_boxes':outside[(group,cls)],
            **{p+'_area_percent':record['relative_area'][p]*100 for p in ('min','p05','p25','median','p75','p95','max')}})
    write_csv(output/'statistics/bounding_box_summary.csv',list(summary_rows[0]),summary_rows)
    write_csv(output/'statistics/image_orientation_audit.csv',[
        'directory','image_path','manifest_width','manifest_height','encoded_width','encoded_height',
        'exif_orientation','oriented_width','oriented_height','manifest_matches_oriented'],dimension_audit)
    verification['exif_swapped_images']=sum(r['exif_orientation'] in (5,6,7,8) for r in dimension_audit)
    verification['manifest_vs_oriented_image_size_mismatches']=sum(not r['manifest_matches_oriented'] for r in dimension_audit)
    if sum(n for (d,_,_),n in samples.items() if d=='public_optical')!=86563:
        raise ValueError('Unexpected public sample count')
    if sum(n for (d,_,_),n in samples.items() if d=='paired_rgbt')!=35859:
        raise ValueError('Unexpected paired sample count')
    expected={'public_optical__fire':67269,'public_optical__smoke':45010,
              'paired_source__fire':49361,'paired_source__smoke':32363}
    if any(len(arrays[k])!=n for k,n in expected.items()):
        raise ValueError('Source class box count differs from frozen release statistics')
    summary={'created_at':datetime.now(timezone(timedelta(hours=9))).isoformat(),
             'sample_totals':{'public_optical_images':86563,'paired_rgbt_pairs':35859,'paired_image_views':71718},
             'negative_target_files':dict(negative),'box_statistics':metrics,'verification':verification,
             'definitions':{'normalised_box_area':'width * height in YOLO normalised coordinates; image-area fraction',
                            'image_resolution':'EXIF-orientation-aware retained image size when image headers are checked; otherwise recorded manifest size',
                            'paired_primary_boxes':'canonical optical targets counted ONCE per pair, not once per modality',
                            'paired_source_boxes':'original source rectangles, retained unmodified even when extending outside the frame',
                            'out_of_frame_box':'a rectangle edge crosses [0,1] by more than 1e-6 in normalised coordinates',
                            'pixel_area':'normalised box area times retained optical width times retained optical height',
                            'scope':'All frozen train/validation/test samples; not model performance or a new split'},
             'annotation_bytes_changed':False,'manifest_bytes_changed':False}
    (output/'statistics/overview_statistics.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary


def render(output):
    from data_overview_figures import render_figures
    return render_figures(Path(output))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--catalog-directory',type=Path)
    p.add_argument('--archive-directory',type=Path,action='append',default=[])
    p.add_argument('--skip-archive-hashes',action='store_true')
    p.add_argument('--verify-image-dimensions',action='store_true')
    p.add_argument('--collect-only',action='store_true')
    p.add_argument('--render-only',action='store_true')
    a=p.parse_args()
    if a.collect_only and a.render_only:
        p.error('Choose collection or rendering, not both')
    if not a.render_only:
        collect(a.repo,a.output,a.catalog_directory,a.archive_directory,not a.skip_archive_hashes,a.verify_image_dimensions)
    if not a.collect_only:
        render(a.output)


if __name__=='__main__':
    main()
