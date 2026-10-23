"""Execute bundled protocol decoders in a bounded separate interpreter."""
import json,subprocess,sys
from pathlib import Path

def decode_capture(config):
    payload=json.dumps(config)
    if len(payload)>1_500_000:raise ValueError('Capture exceeds decoder size limit')
    try:r=subprocess.run([sys.executable,str(Path(__file__).with_name('decode_worker.py'))],input=payload,text=True,capture_output=True,timeout=6)
    except subprocess.TimeoutExpired:raise ValueError('Decoder exceeded six seconds')
    try:result=json.loads(r.stdout)
    except ValueError:raise ValueError('Decoder failed without a valid report')
    if r.returncode or 'error' in result:raise ValueError(result.get('error','Decoder failed'))
    return result
