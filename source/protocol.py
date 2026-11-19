"""版本化研究对象桶，公开 S3 XML 子集。"""
import base64
import hashlib
from urllib.parse import quote
from xml.sax.saxutils import escape
KEY="项目 A/练习 数据.bin"
DATA={("v+2"):("新版实验原件"*40).encode(),("v+1"):("旧版实验原件"*45).encode(),"other":b"independent"}
def checksum(data):return base64.b64encode(hashlib.sha256(data).digest()).decode()
class Source:
    name="研究资料版本桶"
    def versions(self):
        rows=[dict(key=KEY,id="v+2",delete=False),dict(key=KEY,id="v+1",delete=False),dict(key="附件/z.txt",id="other",delete=False)]
        if self.stage>=1:rows.insert(0,dict(key=KEY,id="delete-3",delete=True))
        if self.stage>=2:rows=[r for r in rows if r["id"]!="v+1"]
        return sorted(rows,key=lambda r:r["key"].encode("utf-8"))
    def route(self,method,path,q,headers,body):
        if path=="/research" and "versions" in q:
            rows=self.versions();offset=0
            if q.get("key-marker"):
                matches=[i for i,r in enumerate(rows) if r["key"]==q["key-marker"] and r["id"]==q.get("version-id-marker")]
                if not matches:return 400,{},"续页必须同时匹配键与版本"
                offset=matches[0]+1
            n=max(1,min(2,int(q.get("max-keys","2"))));page=rows[offset:offset+n];truncated=offset+n<len(rows)
            enc=q.get("encoding-type")=="url"
            def key(k):return quote(k,safe="") if enc else escape(k)
            items=[]
            for r in page:
                tag="DeleteMarker" if r["delete"] else "Version"
                latest=next(x for x in rows if x["key"]==r["key"])["id"]==r["id"]
                items.append(f'<{tag}><Key>{key(r["key"])}</Key><VersionId>{r["id"]}</VersionId><IsLatest>{str(latest).lower()}</IsLatest><LastModified>2026-11-16T10:00:00Z</LastModified>'+("" if r["delete"] else f'<ETag>"same-multipart-2"</ETag><Size>{len(DATA[r["id"]])}</Size>')+f"</{tag}>")
            markers=f'<NextKeyMarker>{key(page[-1]["key"])}</NextKeyMarker><NextVersionIdMarker>{page[-1]["id"]}</NextVersionIdMarker>' if truncated else ""
            text='<ListVersionsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>research</Name>'+("<EncodingType>url</EncodingType>" if enc else "")+f"<IsTruncated>{str(truncated).lower()}</IsTruncated>"+"".join(items)+markers+"</ListVersionsResult>"
            return 200,{"Content-Type":"application/xml"},text
        if not path.startswith("/research/"):return 404,{},b""
        from urllib.parse import unquote
        key=unquote(path[len("/research/"):]);version=q.get("versionId")
        rows=[r for r in self.versions() if r["key"]==key]
        row=next((r for r in rows if r["id"]==version),None) if version else (rows[0] if rows else None)
        if not row:return 404,{"x-amz-error-code":"NoSuchVersion"},b""
        if row["delete"]:return (405 if version else 404),{"x-amz-delete-marker":"true","x-amz-version-id":row["id"]},b""
        data=DATA[row["id"]];h={"Content-Type":"application/octet-stream","x-amz-version-id":row["id"],"x-amz-checksum-sha256":checksum(data),"ETag":'"same-multipart-2"',"Accept-Ranges":"bytes"}
        if headers.get("Range") and not self.options.get("ignore_range"):
            spec=headers["Range"].removeprefix("bytes=");start,end=spec.split("-");start=int(start);end=int(end) if end else len(data)-1
            if start>=len(data) or start<0:return 416,{"Content-Range":f"bytes */{len(data)}"},b""
            end=min(end,len(data)-1);h["Content-Range"]=f"bytes {start}-{end}/{len(data)}"
            return 206,h,data[start:end+1]
        return 200,h,data
