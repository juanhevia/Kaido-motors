"""Construye la entrega ZIP sin entornos, credenciales ni archivos temporales."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib,json
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'entrega/modelo_y_datos.zip'
files=[]
for pat in ['*.py','*.md','requirements*.txt','config.json','.gitignore','.gitattributes']:
    files+=list(ROOT.glob(pat))
for folder in ['data','docs','examples','resultados']:
    files += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files=sorted(p for p in set(files) if p.name not in {'METODOLOGIA.md','GUION_PRESENTACION.md'})
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with ZipFile(DEST,'w',ZIP_DEFLATED,compresslevel=9) as z:
    for p in files: z.write(p,Path('kaido-motors-solucion')/p.relative_to(ROOT))
    z.writestr('kaido-motors-solucion/MANIFIESTO_SHA256.json',json.dumps(manifest,indent=2))
with ZipFile(DEST) as z:
    assert z.testzip() is None
    assert len([n for n in z.namelist() if '/data/' in n and n.endswith('.csv')])==7
print(f'{DEST}: {len(files)} archivos, {DEST.stat().st_size:,} bytes')
