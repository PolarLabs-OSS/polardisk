import tempfile
from pathlib import Path
from polardisk import scan,folders_summary,fmt
with tempfile.TemporaryDirectory() as t:
 root=Path(t);(root/'alpha').mkdir();(root/'beta').mkdir()
 (root/'alpha'/'big.bin').write_bytes(b'a'*1024)
 (root/'beta'/'small.txt').write_text('a')
 (root/'top.txt').write_bytes(b'bb')
 data,err=scan(root)
 assert len(data)==3 and err==0
 summary=dict(folders_summary(data,root))
 assert summary['alpha']==1024 and summary['(file nella cartella principale)']==2
 assert fmt(1024)=='1.0 KB'
 print('PASS: scan, folder totals, sizes')
