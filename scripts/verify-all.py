"""Run every repository suite against real engines; retain failures and exit nonzero.

No dependency downloads or skipped suites. Browser suites use port 8765 and run
sequentially. Full logs stay in ignored .state/verification; a compact report is
written to evidence/full-verification.json. Run from any directory.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def dependency_snapshot(env):
    def version(binary, args, optional=False):
        if not binary or not Path(binary).is_file():return dict(available=False,optional=optional,diagnostic='Not installed/configured in this environment.')
        try:
            p=subprocess.run([str(binary),*args],env=env,capture_output=True,text=True,timeout=10)
            return dict(available=p.returncode==0,optional=optional,version=(p.stdout or p.stderr).strip()[:800],exitCode=p.returncode)
        except (OSError,subprocess.TimeoutExpired) as exc:return dict(available=False,optional=optional,diagnostic=str(exc))
    local=ROOT/'.tools/usr/bin'
    spice=env.get('NGSPICE_BIN') or shutil.which('ngspice') or str(local/'ngspice')
    avr=env.get('AVR_GXX_BIN') or shutil.which('avr-g++') or str(local/'avr-g++')
    configured={**env}
    lib=ROOT/'.tools/usr/lib/x86_64-linux-gnu'
    if lib.is_dir():configured['LD_LIBRARY_PATH']=str(lib)+':'+configured.get('LD_LIBRARY_PATH','')
    previous=env;env=configured
    return dict(node=version(shutil.which('node'),['--version']),ngspice=version(spice,['--version']),avrCompiler=version(avr,['--version']),arduinoCli=version(previous.get('ARDUINO_CLI_BIN') or shutil.which('arduino-cli'),['version','--format','json'],True))


def source_fingerprint():
    result=subprocess.run(['git','ls-files','-co','--exclude-standard'],cwd=ROOT,capture_output=True,text=True,check=True)
    digest=hashlib.sha256()
    for name in sorted(set(result.stdout.splitlines())):
        p=ROOT/name
        if p.suffix not in {'.py','.js','.cjs','.json','.css','.html','.cc','.h','.cpp','.ino','.hex','.uf2','.yml','.mjs','.gz','.woff','.woff2','.ttf','.png','.txt'} or name.startswith(('screenshots/','evidence/')):continue
        digest.update(name.encode()+b'\0'+p.read_bytes()+b'\0')
    return digest.hexdigest()


def main():
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8765))==0:
            print('Port 8765 is in use. Stop the local workbench before running the browser suites.',flush=True)
            return 1
    os.chdir(ROOT);env=os.environ.copy()
    if not env.get('ARDUINO_CLI_BIN') and (ROOT/'.tools/arduino-cli').is_file():env['ARDUINO_CLI_BIN']=str(ROOT/'.tools/arduino-cli')
    logs=ROOT/'.state/verification';logs.mkdir(parents=True,exist_ok=True)
    sha=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','status','--porcelain'],capture_output=True,text=True,check=True).stdout.strip())
    dependencies=dependency_snapshot(env)
    checks=[('circuitjs-upstream',[sys.executable,'scripts/test-circuitjs-upstream.py']),
            ('native-peripherals',[sys.executable,'scripts/build-picsimlab.py']),
            ('python',[sys.executable,'-m','unittest','discover','-s','tests','-v']),
            ('node',['node','--test',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('test_*.cjs'))]])]
    for p in sorted((ROOT/'web').glob('*.js')):checks.append(('syntax-'+p.stem,['node','--check',str(p.relative_to(ROOT))]))
    for p in sorted((ROOT/'tests').glob('*browser.cjs')):checks.append((p.stem,['node',str(p.relative_to(ROOT))]))
    results=[];started=time.monotonic();source_before=source_fingerprint()
    for label,command in checks:
        begin=time.monotonic();print('RUN '+label,flush=True)
        try:
            p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=240)
            output=p.stdout+p.stderr;code=p.returncode
        except subprocess.TimeoutExpired as exc:
            output=str(exc);code=124
        (logs/(label+'.log')).write_text(output)
        count=re.search(r'Ran (\d+) tests?',output) if label=='python' else re.search(r'(?:#|ℹ) tests (\d+)',output) if label=='node' else re.search(r'Tests\s+(\d+) passed',output) if label=='circuitjs-upstream' else None
        skipped=re.search(r'(?:#|ℹ) skipped (\d+)',output)
        status='passed' if code==0 else 'failed'
        if re.search(r'OK \(skipped=',output) or skipped and int(skipped[1])>0:status='incomplete'
        results.append(dict(name=label,command=command,status=status,exitCode=code,seconds=round(time.monotonic()-begin,3),testCount=int(count[1]) if count else None,log='.state/verification/'+label+'.log'))
        print(f'{status.upper()} {label} ({results[-1]["seconds"]} s)',flush=True)
        if status!='passed':print(output[-3500:],flush=True)
    source_after=source_fingerprint()
    if source_before!=source_after:
        results.append(dict(name='source-stability',command=[],status='failed',exitCode=1,seconds=0,testCount=None,diagnostic='Source changed during verification. Run the matrix again without editing source files.'))
    report=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseCommit=sha,workingTreeModified=dirty,sourceSha256=source_before,sourceStable=source_before==source_after,platform=sys.platform,python=sys.version.split()[0],checks=results,seconds=round(time.monotonic()-started,3),allPassed=all(r['status']=='passed' for r in results),unitTests=sum(r['testCount'] or 0 for r in results),browserSuites=sum(r['name'].endswith('browser') for r in results),scope='Internal solver, firmware and browser regression tests; no physical validation, public hosting or Proteus parity certification.')
    report['dependencies']=dependencies
    report['unverifiedCapabilities']=[
        'Live Arduino CLI registry search/download/install (local CLI status and bounded command/diagnostic handling are tested).',
        'External Renode firmware execution (launch-profile export only).',
        'Physical device accuracy, Windows/macOS toolchain/installer operation and hardware upload.',
        'General MCU/analog closed-loop co-simulation, ESP32/STM32/PIC/Raspberry Pi Linux execution, PCB routing and Proteus import (not implemented).']
    report['claim']='All discovered regression suites passed.' if report['allPassed'] else 'Regression verification incomplete or failed.'
    target=ROOT/'evidence/full-verification.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['allPassed','unitTests','browserSuites','seconds']}),flush=True)
    return 0 if report['allPassed'] else 1


if __name__=='__main__':sys.exit(main())
