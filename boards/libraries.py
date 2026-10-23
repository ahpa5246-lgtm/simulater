"""Bounded local source-library installation. ZIPs never execute installer code."""
import io
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

DEFAULT_ROOT=Path(os.environ.get('MINA_LIBRARY_DIR',Path(__file__).resolve().parents[1]/'.state/libraries'))
ALLOWED={'.h','.hpp','.c','.cpp','.cc','.s','.S','.txt','.md','.properties','.json','.ino','.csv','.keywords'}

def list_libraries(root=None):
    root=Path(root or DEFAULT_ROOT)
    if not root.exists():return []
    results=[]
    for folder in sorted(root.iterdir()):
        if folder.is_dir() and not folder.name.startswith('.'):
            props={}
            metadata=folder/'library.properties'
            if metadata.exists():
                for line in metadata.read_text(errors='replace').splitlines():
                    if '=' in line:
                        key,value=line.split('=',1);props[key.strip()]=value.strip()
            results.append({'id':folder.name,'name':props.get('name',folder.name),'version':props.get('version','local'),'license':props.get('license','See included license'),'headers':[str(p.relative_to(folder)) for p in folder.rglob('*.h')][:30]})
    return results

def install_library(data,root=None):
    if not isinstance(data,bytes) or not 1<=len(data)<=1_000_000:raise ValueError('Library ZIP must be smaller than 1 MB.')
    root=Path(root or DEFAULT_ROOT);root.mkdir(parents=True,exist_ok=True)
    try:archive=zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:raise ValueError('Invalid library ZIP.')
    with archive:
        files=archive.infolist()
        if not files or len(files)>200 or sum(f.file_size for f in files)>3_000_000:raise ValueError('Library archive exceeds file or size limits.')
        for info in files:
            path=PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Unsafe path or symbolic link in library ZIP.')
            if not info.is_dir() and (path.suffix not in ALLOWED and path.name.upper() not in {'LICENSE','COPYING','NOTICE','AUTHORS'}):
                raise ValueError(f'Unsupported library file: {path.name}. Only source and documentation are accepted.')
        with tempfile.TemporaryDirectory(dir=root,prefix='.install-') as temp:
            temp=Path(temp)
            for info in files:
                destination=temp.joinpath(*PurePosixPath(info.filename).parts)
                if info.is_dir():destination.mkdir(parents=True,exist_ok=True)
                else:destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(archive.read(info))
            metadata=list(temp.rglob('library.properties'))
            if len(metadata)!=1:raise ValueError('ZIP must contain exactly one Arduino library.properties file.')
            folder=metadata[0].parent
            if not list(folder.rglob('*.h')):raise ValueError('Library has no C/C++ header files.')
            props={line.split('=',1)[0].strip():line.split('=',1)[1].strip() for line in metadata[0].read_text().splitlines() if '=' in line}
            name=props.get('name','')
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]{0,63}',name):raise ValueError('Invalid library name.')
            key=re.sub(r'[^A-Za-z0-9_-]','_',name);target=root/key
            if target.exists():raise ValueError('This library is already installed; existing files were not overwritten.')
            folder.rename(target)
    return next(item for item in list_libraries(root) if item['id']==key)
