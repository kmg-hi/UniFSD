"""Static scientific figures from audited, unchanged dataset records."""

import csv
import json
from collections import Counter
from pathlib import Path


def read_rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def write_rows(path,fields,records):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def render_figures(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    from PIL import Image

    output=Path(output)
    figures=output/'figures'
    figures.mkdir(exist_ok=True)
    stats=output/'statistics'
    sample_rows=read_rows(stats/'sample_counts.csv')
    resolutions=read_rows(stats/'image_resolutions.csv')
    arrays=np.load(output/'private/box_geometry.npz')
    plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.titlesize':10,
        'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
        'legend.fontsize':8,'axes.linewidth':.7,'axes.spines.top':False,
        'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','savefig.facecolor':'white','axes.facecolor':'white',
        'text.color':'#20262C','axes.labelcolor':'#20262C','xtick.color':'#374151','ytick.color':'#374151'})
    colors={'fire':'#D55E00','smoke':'#0072B2'}
    saved=[]
    layout=[]

    def export(fig,name):
        fig.canvas.draw()
        bounds=fig.bbox
        renderer=fig.canvas.get_renderer()
        outside=[]
        for text in fig.findobj(matplotlib.text.Text):
            if not text.get_visible() or not text.get_text():
                continue
            box=text.get_window_extent(renderer)
            if box.x0<bounds.x0-3 or box.y0<bounds.y0-3 or box.x1>bounds.x1+3 or box.y1>bounds.y1+3:
                outside.append(text.get_text())
        for extension in ('png','pdf','svg','tif'):
            path=figures/(name+'.'+extension)
            kwargs={'dpi':600,'bbox_inches':'tight','pad_inches':.08}
            if extension=='tif':
                kwargs['pil_kwargs']={'compression':'tiff_lzw'}
            fig.savefig(path,**kwargs)
        with Image.open(figures/(name+'.png')) as image:
            tiny=np.asarray(image.convert('RGB').resize((600,400)))
            nonwhite=float(np.mean(np.any(tiny<240,axis=2)))
            if nonwhite<.015:
                raise ValueError('Blank or almost empty plot: '+name)
            saved.append({'name':name,'png_size':image.size,'nonwhite_fraction':nonwhite})
        layout.append({'name':name,'outside_base_canvas_text':outside,
                       'note':'Exports use tight bounding boxes; every PNG still requires visual review.'})
        plt.close(fig)

    # Sample units are intentionally shown on different axes: images versus pairs.
    fig,axes=plt.subplots(1,2,figsize=(7.6,3.7))
    fig.subplots_adjust(left=.09,right=.98,bottom=.22,top=.79,wspace=.42)
    split_colors={'train':'#0072B2','val':'#009E73','test':'#E69F00'}
    handles=[]
    for i,(dataset,components,labels,title,unit) in enumerate((
        ('public_optical',['FASDD_CV','D-Fire','CQU','Roboflow_FireSmoke'],['FASDD_CV','D-Fire','CQU','Roboflow'],
         '(a) Single-modal optical: 86,563 images','Optical images'),
        ('paired_rgbt',['real','synthetic'],['Real','Unity synthetic'],
         '(b) Optical-thermal: 35,859 pairs','Optical-thermal pairs'))):
        ax=axes[i]
        totals=np.zeros(len(components))
        x=np.arange(len(components))
        for split in ('train','val','test'):
            values=np.array([sum(int(r['samples']) for r in sample_rows
                if r['dataset']==dataset and r['component']==c and r['split']==split) for c in components])
            bars=ax.bar(x,values,bottom=totals,width=.61,color=split_colors[split],edgecolor='white',linewidth=.45,label=split.title())
            if i==0:
                handles.append(bars)
            totals+=values
        for xx,total in zip(x,totals):
            ax.annotate(f'{int(total):,}',(xx,total),xytext=(0,4),textcoords='offset points',ha='center',fontsize=8)
        ax.set_xticks(x,labels)
        ax.set_ylabel(unit)
        ax.set_title(title,loc='left',fontweight='bold',pad=11,fontsize=9.5)
        ax.set_ylim(0,totals.max()*1.2)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{int(value):,}'))
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.grid(axis='y',color='#E1E5E9',linewidth=.5)
        ax.set_axisbelow(True)
    fig.legend(handles,['Train','Validation','Test'],loc='upper center',bbox_to_anchor=(.53,.99),ncol=3,frameon=False)
    export(fig,'01_final_dataset_scale')

    # Every point is an exact retained (width,height) combination, not a bin centre.
    fig,axes=plt.subplots(1,3,figsize=(8.0,3.55))
    fig.subplots_adjust(left=.075,right=.985,bottom=.20,top=.83,wspace=.28)
    panels=(('public_optical','optic','(a) Single-modal optical','#5B6770'),
            ('paired_rgbt','optic','(b) Paired optical','#0072B2'),
            ('paired_rgbt','thermal','(c) Paired thermal','#009E73'))
    all_width=[int(r['width']) for r in resolutions]
    all_height=[int(r['height']) for r in resolutions]
    low=2**np.floor(np.log2(min(all_width+all_height)))
    high=2**np.ceil(np.log2(max(all_width+all_height)))
    ticks=[2**power for power in range(int(np.log2(low)),int(np.log2(high))+1)]
    if len(ticks)>7:
        ticks=ticks[::2]
    for panel_index,(ax,(dataset,modality,title,color)) in enumerate(zip(axes,panels)):
        counts=Counter()
        for row in resolutions:
            if row['dataset']==dataset and row['modality']==modality:
                counts[(int(row['width']),int(row['height']))]+=int(row['images'])
        xy=np.array(list(counts))
        n=np.array(list(counts.values()))
        ax.scatter(xy[:,0],xy[:,1],s=3+500*n/n.sum(),c=color,alpha=.62,edgecolors='white',linewidths=.3,zorder=3)
        positions=((.43,.57),(.51,.10),(.53,.83)) if panel_index==0 else ((.67,.58),(.12,.10),(.06,.59))
        for ((width,height),count),position in zip(counts.most_common(3),positions):
            ax.annotate(f'{width} x {height}\n{count/n.sum():.1%}',(width,height),xytext=position,textcoords='axes fraction',
                        fontsize=7,ha='left',va='center',color='#20262C',
                        bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':1.2},
                        arrowprops={'arrowstyle':'-','color':'#818992','lw':.5},zorder=5)
        ax.set_xscale('log',base=2)
        ax.set_yscale('log',base=2)
        ax.set_xlim(low*.8,high*1.2)
        ax.set_ylim(low*.8,high*1.2)
        ax.set_xticks(ticks,[str(int(x)) for x in ticks],rotation=35,ha='right')
        ax.set_yticks(ticks,[str(int(x)) for x in ticks])
        ax.set_xlabel('Width (pixels)')
        ax.set_title(title+f'\nn = {int(n.sum()):,} images',loc='left',fontweight='bold',fontsize=9.4,pad=12)
        ax.grid(which='major',color='#E3E7EB',linewidth=.45)
        ax.set_axisbelow(True)
    axes[0].set_ylabel('Height (pixels)')
    export(fig,'02_image_resolution')

    groups=('public_optical','paired_source')
    data={(group,cls):arrays[group+'__'+cls] for group in groups for cls in ('fire','smoke')}
    max_w=max(float(a[:,0].max()) for a in data.values())
    max_h=max(float(a[:,1].max()) for a in data.values())
    x_end=max(1.,np.ceil(max_w*10)/10)
    y_end=max(1.,np.ceil(max_h*10)/10)
    x_edges=np.linspace(0,x_end,51)
    y_edges=np.linspace(0,y_end,51)
    matrices={key:np.histogram2d(a[:,0],a[:,1],bins=(x_edges,y_edges))[0] for key,a in data.items()}
    if any(int(matrices[key].sum())!=len(a) for key,a in data.items()):
        raise ValueError('Histogram omitted source boxes')
    vmax=max(int(m.max()) for m in matrices.values())
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.1),sharex=True,sharey=True)
    fig.subplots_adjust(left=.105,right=.84,bottom=.10,top=.90,wspace=.14,hspace=.30)
    bin_rows=[]
    for i,((group,cls),a) in enumerate(data.items()):
        ax=axes.flat[i]
        histogram=matrices[(group,cls)]
        image=ax.pcolormesh(x_edges*100,y_edges*100,np.ma.masked_less(histogram.T,1),
                           cmap='cividis',norm=LogNorm(vmin=1,vmax=vmax),shading='flat',rasterized=True)
        record='Single-modal optical' if group=='public_optical' else 'Paired source annotations'
        ax.set_title(f'({chr(97+i)}) {record}\n{cls.title()}   n = {len(a):,}',loc='left',fontsize=9.5,pad=8)
        ax.set_xlim(0,x_end*100)
        ax.set_ylim(0,y_end*100)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(5))
        if x_end>1:
            ax.axvline(100,c='#B6B9BE',lw=.6,ls='--')
        if y_end>1:
            ax.axhline(100,c='#B6B9BE',lw=.6,ls='--')
        for ix,iy in np.argwhere(histogram>0):
            bin_rows.append({'group':group,'class':cls,'width_left_percent':x_edges[ix]*100,
                'width_right_percent':x_edges[ix+1]*100,'height_left_percent':y_edges[iy]*100,
                'height_right_percent':y_edges[iy+1]*100,'boxes':int(histogram[ix,iy])})
    for ax in axes[:,0]:
        ax.set_ylabel('Box height / image height (%)')
    for ax in axes[-1,:]:
        ax.set_xlabel('Box width / image width (%)')
    cax=fig.add_axes([.88,.17,.022,.64])
    colorbar=fig.colorbar(image,cax=cax,label='Bounding boxes per bin (log scale)')
    colorbar.set_ticks([10**p for p in range(int(np.floor(np.log10(vmax)))+1)])
    colorbar.ax.minorticks_off()
    write_rows(stats/'box_width_height_bins.csv',list(bin_rows[0]),bin_rows)
    export(fig,'03_bounding_box_size')

    # Supplementary comparison keeps original and clipped targets explicitly separate.
    groups=('public_optical','paired_source','paired_canonical')
    labels=('(a) Single-modal optical','(b) Paired source rectangles','(c) Paired canonical targets')
    min_area=min(float(arrays[g+'__'+c][:,2].min())*100 for g in groups for c in ('fire','smoke'))
    max_area=max(float(arrays[g+'__'+c][:,2].max())*100 for g in groups for c in ('fire','smoke'))
    edges=np.geomspace(min_area*.99,max_area*1.01,43)
    fig,axes=plt.subplots(1,3,figsize=(8.1,3.45),sharex=True,sharey=True)
    fig.subplots_adjust(left=.08,right=.985,bottom=.20,top=.82,wspace=.16)
    histogram_rows=[]
    for ax,group,title in zip(axes,groups,labels):
        for cls in ('fire','smoke'):
            areas=arrays[group+'__'+cls][:,2]*100
            counts,_=np.histogram(areas,bins=edges)
            if counts.sum()!=len(areas):
                raise ValueError('Area histogram omitted boxes')
            percent=counts/len(areas)*100
            median=float(np.median(areas))
            ax.stairs(percent,edges,color=colors[cls],lw=1.4,label=f'{cls.title()} (n={len(areas):,})')
            ax.axvline(median,color=colors[cls],lw=.8,ls='--',alpha=.75)
            for i,count in enumerate(counts):
                histogram_rows.append({'group':group,'class':cls,'area_left_percent':edges[i],
                    'area_right_percent':edges[i+1],'boxes':int(count),'percent_of_class':percent[i]})
        ax.set_xscale('log')
        ax.set_xlim(edges[0],edges[-1])
        ax.set_xticks([10.**p for p in range(int(np.ceil(np.log10(edges[0]))),int(np.floor(np.log10(edges[-1])))+1)])
        ax.set_xlabel('Box area / image area (%)')
        ax.set_title(title,loc='left',fontweight='bold',fontsize=9.2,pad=10)
        ax.legend(frameon=False,fontsize=7.5,loc='upper left')
        ax.grid(axis='y',color='#E1E5E9',linewidth=.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel('Boxes per logarithmic bin (%)')
    axes[0].set_ylim(0,max(float(r['percent_of_class']) for r in histogram_rows)*1.33)
    write_rows(stats/'box_area_bins.csv',list(histogram_rows[0]),histogram_rows)
    export(fig,'S1_box_area_source_vs_training')
    report={'figures':saved,'layout':layout,'main_figures':3,'supplementary_figures':1,
            'source_boxes_not_clipped_or_filtered':True,'paired_modality_copies_not_double_counted':True,
            'all_bins_account_for_all_plotted_boxes':True}
    (output/'figure_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'stage':'figures_rendered','main':3,'supplementary':1,'formats':['png','pdf','svg','tif']}),flush=True)
    return report
