"""Losslessly package newly produced matrices, preserving raw originals outside Git.

One new matrix exceeds GitHub's single-file limit. Deterministic gzip avoids LFS
and does not alter any XML byte, mutation identity fields or test identity.
"""
import gzip,hashlib,shutil,tempfile
from pathlib import Path
from derive import ITER,ROOT,read,write
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 manifest=ITER/'matrix_packaging.json'
 previous=read(manifest) if manifest.exists() else {'files':[]}
 archive=Path(tempfile.mkdtemp(prefix='pit-unify-raw-matrices-',dir='/private/tmp'));rows={r['path']:r for r in previous['files']};count=0
 for subject in ('jgrapht','spring-core'):
  for raw in sorted((ITER/'pit'/subject/'per-class').glob('*/mutations.xml')):
   packed=raw.with_suffix('.xml.gz');rawhash=digest(raw);target=archive/subject/raw.parent.name/raw.name
   with raw.open('rb') as inp,packed.open('wb') as out:
    with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:shutil.copyfileobj(inp,gz)
   h=hashlib.sha256()
   with gzip.open(packed,'rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
   assert h.hexdigest()==rawhash
   key=str(packed.relative_to(ROOT));rows[key]={'path':key,'rawSha256':rawhash,'gzipSha256':digest(packed),'rawBytes':raw.stat().st_size,'gzipBytes':packed.stat().st_size,'rawOriginal':str(target),'decompressedBytesIdentical':True};count+=1
   target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(raw),str(target))
 write(manifest,{'reason':'Lossless compression for GitHub single-file size limit; all original XML bytes preserved.','files':list(rows.values())})
 print('PACKAGED',count,'new matrices;',len(rows),'total; exact decompressed bytes verified')
if __name__=='__main__':main()
