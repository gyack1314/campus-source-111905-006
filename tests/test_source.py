from tests.support import SourceCase
from source.protocol import KEY,DATA,checksum
from urllib.parse import quote,urlencode
import xml.etree.ElementTree as E
N={"s":"http://s3.amazonaws.com/doc/2006-03-01/"}
class Contract(SourceCase):
    def object(self,v=None,**headers):
        return self.request("/research/"+quote(KEY,safe="/")+("?"+urlencode({"versionId":v}) if v else ""),headers=headers)
    def test_version_directory_pair(self):
        self.control(1);s,h,b=self.request("/research?versions=&encoding-type=url")
        root=E.fromstring(b);self.assertEqual(root.findtext("s:IsTruncated",namespaces=N),"true")
        self.assertEqual(root.findtext("s:NextVersionIdMarker",namespaces=N),"v+2")
    def test_delete_marker_not_empty_file(self):
        self.control(1)
        self.assertEqual(self.object()[0],404)
        self.assertEqual(self.object("delete-3")[0],405)
        self.assertEqual(self.object("v+1")[0],200)
    def test_marker_requires_both(self):
        self.assertEqual(self.request("/research?"+urlencode({"versions":"","key-marker":KEY}))[0],400)
    def test_encoding_and_version(self):
        s,h,b=self.object("v+1");self.assertEqual(s,200);self.assertEqual(b,DATA["v+1"])
        self.assertEqual(h["x-amz-version-id"],"v+1")
    def test_range_and_checksum(self):
        s,h,b=self.object("v+1",Range="bytes=10-19")
        self.assertEqual(s,206);self.assertEqual(b,DATA["v+1"][10:20])
        self.assertEqual(h["Content-Range"],f"bytes 10-19/{len(DATA['v+1'])}")
        self.assertEqual(h["x-amz-checksum-sha256"],checksum(DATA["v+1"]))
    def test_range_ignored(self):
        self.control(0,ignore_range=True)
        s,h,b=self.object("v+1",Range="bytes=10-19");self.assertEqual(s,200);self.assertEqual(b,DATA["v+1"])
    def test_permanent_retention(self):
        self.control(2);self.assertEqual(self.object("v+1")[0],404);self.assertEqual(self.object("v+2")[0],200)
    def test_same_etag_different_content(self):
        a=self.object("v+1");b=self.object("v+2")
        self.assertEqual(a[1]["ETag"],b[1]["ETag"]);self.assertNotEqual(a[2],b[2])
