"""Record lossless storage for duplicate raw XML exceeding GitHub's limit."""
import gzip,hashlib
from common import *
rows=[]
for row in read(C/'matrix_packaging.json'):
    source=ROOT/row['source'];packed=ROOT/row['packaged']
    assert hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()==sha(source)==row['sourceSha256']
    if source.stat().st_size>100_000_000:
        rows.append({**row,'sourceBytes':source.stat().st_size,'repositoryRepresentation':'existing byte-exact gzip; duplicate raw file remains local, not staged'})
write(OUT/'storage_manifest.json',{'reason':'GitHub single-file limit; no verified C file is rewritten or removed locally. Canonical PIT inputs already use the verified gzip. The new verifier accepts byte-identical decompression if a duplicate raw file is absent in a fresh clone.','omittedDuplicateRawFiles':rows})
print('PASS: lossless transport verified;',len(rows),'oversized duplicate raw XML files kept locally')
