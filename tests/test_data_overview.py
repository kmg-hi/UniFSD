import hashlib
import importlib.util
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from publication import ROOT
from plot_data_overview import FrozenReader,collect,parse_yolo


class DataOverviewTests(unittest.TestCase):
    def setUp(self):
        target=ROOT/'.local/test-tmp'
        target.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=target)
        self.root=Path(self.temp.name)
        self.base=self.root/'public optical'
        (self.base/'labels').mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_label_has_no_boxes(self):
        self.assertEqual(parse_yolo(b''),[])
        self.assertEqual(parse_yolo(b'\n\r\n'),[])

    def test_relative_geometry_and_class_are_preserved(self):
        values=parse_yolo(b'1 0.5 0.4 0.2 0.3\n')
        self.assertEqual(values,[(1,.5,.4,.2,.3)])

    def test_original_outside_frame_boxes_are_not_clipped(self):
        self.assertEqual(parse_yolo(b'0 -0.1 0.5 1.2 0.8\n'),[(0,-.1,.5,1.2,.8)])

    def test_bad_annotations_are_not_silently_dropped(self):
        for raw in (b'0 0.5 0.5 0 0.3',b'0 0.5 0.5 -0.2 0.3',
                    b'2 0.5 0.5 0.2 0.3',b'0 nan 0.5 0.2 0.3',b'0 0.5 0.2'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                parse_yolo(raw)

    def test_label_bytes_must_match_recorded_hash(self):
        raw=b'0 0.5 0.5 0.2 0.3\n'
        label=self.base/'labels/a.txt'
        label.write_bytes(raw)
        with ExitStack() as stack:
            reader=FrozenReader(stack,self.root,'public optical',None,[],False)
            self.assertEqual(reader.label('labels/a.txt',hashlib.sha256(raw).hexdigest())[0],raw)
            with self.assertRaises(ValueError):
                reader.label('labels/a.txt','0'*64)
        self.assertEqual(label.read_bytes(),raw)

    def test_reader_rejects_parent_traversal(self):
        with ExitStack() as stack:
            reader=FrozenReader(stack,self.root,'public optical',None,[],False)
            for value in ('../outside','/absolute','a\\b','a/../b'):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    reader.open(value)

    @unittest.skipUnless(importlib.util.find_spec('numpy'),'Optional NumPy is not installed')
    def test_figure_output_cannot_overwrite_dataset_metadata(self):
        target=self.base/'metadata'
        with self.assertRaisesRegex(ValueError,'protected'):
            collect(self.root,target)
        self.assertFalse(target.exists())

    @unittest.skipUnless(importlib.util.find_spec('PIL'),'Optional Pillow is not installed')
    def test_dimensions_respect_exif_without_rewriting_image(self):
        from PIL import Image
        path=self.base/'rotated.jpg'
        exif=Image.Exif()
        exif[274]=8
        Image.new('RGB',(2,4)).save(path,exif=exif)
        before=path.read_bytes()
        with ExitStack() as stack:
            reader=FrozenReader(stack,self.root,'public optical',None,[],False)
            self.assertEqual(reader.dimensions('rotated.jpg',(4,2)),(4,2))
            self.assertTrue(reader.dimension_audit[0]['manifest_matches_oriented'])
        self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':
    unittest.main()
