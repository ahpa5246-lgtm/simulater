"""Constrain AVR preprocessing inputs and reject assembler file-read directives.

This is a compiler-input policy, not an OS sandbox. The local toolchain and
Arduino core are trusted installations. Do not expose this service publicly.
"""
import ast
import re
import shlex
from pathlib import Path
try:
    import resource
except ImportError:
    resource=None


def check_preprocessed(preprocessed,dependencies,allowed_roots):
    roots=[Path(root).resolve() for root in allowed_roots]
    dependency_text=Path(dependencies).read_text().replace('\\\n',' ')
    if ':' not in dependency_text:raise ValueError('Unable to validate compiler include dependencies.')
    for name in shlex.split(dependency_text.split(':',1)[1]):
        path=Path(name).resolve()
        if not any(path==root or path.is_relative_to(root) for root in roots):
            raise ValueError('Sketch or library attempted an include outside the permitted compiler source directories.')
    code=Path(preprocessed).read_text(errors='replace')
    if len(code)>4_000_000:raise ValueError('Preprocessed source exceeds the size limit.')
    # GCC folds adjacent literal strings in inline assembly. Decode and join
    # them before looking for .incbin/.include, including escaped spellings.
    strings=[]
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"',code,re.S):
        try:strings.append(ast.literal_eval(match.group()))
        except (ValueError,SyntaxError):strings.append(match.group())
    expanded=''.join(strings)
    if re.search(r'\.(?:incbin|include)\b',expanded,re.I):
        raise ValueError('Assembler file-read directives are not allowed in sketches or installed libraries.')


def source_limits():
    if resource is not None:
        resource.setrlimit(resource.RLIMIT_FSIZE,(8_000_000,8_000_000))
        resource.setrlimit(resource.RLIMIT_CPU,(10,10))
