"""Board execution and local Arduino AVR compilation adapters."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from .libraries import DEFAULT_ROOT, list_libraries
from .compile_policy import check_preprocessed, source_limits

ROOT=Path(__file__).resolve().parents[1]
BUILD_LOCK=threading.Lock()

def board_catalogue():
    return [
        {'id':'arduino-uno','name':'Arduino Uno R3','chip':'ATmega328P · 16 MHz','state':'ready','engine':'AVR8js','detail':'HEX execution, ADC, timers, UART, GPIO and LM75 I²C subset.'},
        {'id':'arduino-nano','name':'Arduino Nano (classic)','chip':'ATmega328P · 16 MHz','state':'ready','engine':'AVR8js','detail':'Uses the ATmega328P model; A0–A5 inputs supported.'},
        {'id':'raspberry-pi-pico','name':'Raspberry Pi Pico','chip':'RP2040 · Cortex-M0+','state':'experimental','engine':'RP2040js','detail':'Single-core application-entry UF2 experiment; no ROM boot or SDK compatibility guarantee.'},
        {'id':'raspberry-pi-4','name':'Raspberry Pi 4 / 5','chip':'Linux single-board computer','state':'planned','engine':'Not integrated','detail':'Requires an OS/system emulator, not an AVR/Pico CPU model.'},
        {'id':'esp32','name':'ESP32 / ESP32-C3','chip':'Xtensa / RISC-V variants','state':'planned','engine':'Not integrated','detail':'Exact chip, peripherals and radio models must be verified.'},
        {'id':'stm32','name':'STM32 boards','chip':'ARM Cortex-M families','state':'planned','engine':'Renode candidate','detail':'No executable adapter installed yet.'},
        {'id':'pic','name':'PIC / dsPIC boards','chip':'Microchip families','state':'planned','engine':'PICSimLab candidate','detail':'No executable adapter installed yet.'}]

def run_board(config):
    if not isinstance(config,dict):raise ValueError('Invalid board request.')
    if config.get('board') not in {'arduino-uno','arduino-nano','raspberry-pi-pico'}:raise ValueError('This board is not supported by an installed adapter yet.')
    node=shutil.which('node')
    if not node:raise RuntimeError('Node.js 18+ is required for board simulation.')
    proc=subprocess.run([node,str(ROOT/'boards/runner.cjs')],input=json.dumps(config),capture_output=True,text=True,timeout=15,cwd=ROOT)
    try:result=json.loads(proc.stdout)
    except ValueError:raise RuntimeError('Board engine unavailable. Run npm ci. '+proc.stderr[-500:])
    if proc.returncode or 'error' in result:raise ValueError(result.get('error','Board simulation failed.'))
    return result

def tool(name):
    env_name={'avr-gcc':'AVR_GCC_BIN','avr-g++':'AVR_GXX_BIN','avr-objcopy':'AVR_OBJCOPY_BIN'}[name]
    path=os.environ.get(env_name) or shutil.which(name)
    if path:return path
    local=ROOT/'.tools/usr/bin'/name
    if local.exists():return str(local)
    relocated=ROOT/'.tools/usr/lib/avr/bin'/name.removeprefix('avr-')
    if relocated.exists():return str(relocated)
    raise RuntimeError(f'{name} is missing. Install the AVR toolchain and Arduino AVR core.')

def core_root():
    candidates=[os.environ.get('ARDUINO_AVR_ROOT'),ROOT/'.tools/usr/share/arduino/hardware/arduino/avr','/usr/share/arduino/hardware/arduino/avr']
    for candidate in candidates:
        if candidate and (Path(candidate)/'cores/arduino/Arduino.h').exists():return Path(candidate)
    raise RuntimeError('Arduino AVR core not found. Set ARDUINO_AVR_ROOT to its directory.')

def compile_sketch(source,library_root=None,board="arduino-uno"):
    if board not in {"arduino-uno","arduino-nano"}:raise ValueError("Source compilation is supported only for Uno and classic Nano.")
    if not isinstance(source,str) or not 1<=len(source)<=60000:raise ValueError('Sketch must contain 1–60,000 characters.')
    core=core_root();cc,cpp,objcopy=(tool(n) for n in ('avr-gcc','avr-g++','avr-objcopy'))
    libraries=Path(library_root or DEFAULT_ROOT)
    include_dirs=[core/'cores/arduino',core/('variants/eightanaloginputs' if board=='arduino-nano' else 'variants/standard')]
    sources=list((core/'cores/arduino').glob('*.c'))+list((core/'cores/arduino').glob('*.cpp'))+list((core/'cores/arduino').glob('*.S'))
    # Compile only libraries requested by sketch/header includes, including their dependencies.
    import re
    available=[p for p in (core/'libraries').iterdir() if p.is_dir()]
    if libraries.exists():available += [p for p in libraries.iterdir() if p.is_dir() and not p.name.startswith('.')]
    text=source;chosen=set()
    for _ in range(20):
        wanted=set(re.findall(r'#\s*include\s*[<"]([^">]+)[">]',text));found=False
        for folder in available:
            if folder in chosen:continue
            headers=list(folder.rglob('*.h'))
            if any(h.name in wanted for h in headers):
                chosen.add(folder);found=True
                base=folder/'src' if (folder/'src').is_dir() else folder
                include_dirs.append(base)
                sources += [p for p in base.rglob('*') if p.suffix in {'.c','.cpp','.S'} and not {'examples','test','tests'}&set(p.relative_to(base).parts)]
                text+='\n'+'\n'.join(h.read_text(errors='replace') for h in headers)
        if not found:break
    common=['-mmcu=atmega328p','-DF_CPU=16000000L','-DARDUINO=10819',('-DARDUINO_AVR_NANO' if board=='arduino-nano' else '-DARDUINO_AVR_UNO'),'-DARDUINO_ARCH_AVR','-Os','-ffunction-sections','-fdata-sections']
    for path in include_dirs:common+=['-I',str(path)]
    if len(sources)>100:raise ValueError('Build exceeds the limit of 100 source files.')
    with BUILD_LOCK,tempfile.TemporaryDirectory(prefix='mina-avr-') as folder:
        deadline=time.monotonic()+30
        folder=Path(folder);sketch=folder/'sketch.cpp';sketch.write_text('#include <Arduino.h>\n'+source);sources.append(sketch);objects=[]
        def execute(command,preprocess=False):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ValueError('Build exceeded the 30-second time limit.')
            proc=subprocess.run(command,capture_output=True,text=True,timeout=min(20,remaining),**({'preexec_fn':source_limits} if os.name=='posix' else {}))
            if proc.returncode:
                if preprocess:raise ValueError('Preprocessing failed. Check source includes and syntax; compiler output is withheld until dependency validation.')
                raise ValueError('Compile error:\n'+proc.stderr[-4000:])
        for i,path in enumerate(sources):
            out=folder/f'object{i}.o';compiler=cpp if path.suffix=='.cpp' else cc
            flags=['-std=gnu++11','-fno-exceptions','-fno-threadsafe-statics'] if path.suffix=='.cpp' else []
            if not path.resolve().is_relative_to(core.resolve()):
                if path.suffix not in {'.c','.cpp'}:raise ValueError('Installed assembly source files are not supported.')
                preprocessed=folder/f'checked{i}{".ii" if path.suffix==".cpp" else ".i"}'
                dependency=folder/f'dependencies{i}.d'
                execute([compiler,*common,*flags,'-E','-MD','-MF',str(dependency),str(path),'-o',str(preprocessed)],preprocess=True)
                allowed=[folder,core,libraries,ROOT/'.tools/usr','/usr/lib/avr','/usr/lib/gcc/avr']
                check_preprocessed(preprocessed,dependency,allowed)
                execute([compiler,*common,*flags,'-c',str(preprocessed),'-o',str(out)])
            else:
                execute([compiler,*common,*flags,'-c',str(path),'-o',str(out)])
            objects.append(str(out))
        elf=folder/'firmware.elf';hexfile=folder/'firmware.hex'
        execute([cpp,'-mmcu=atmega328p','-Os','-Wl,--gc-sections',*objects,'-lm','-o',str(elf)])
        execute([objcopy,'-O','ihex','-R','.eeprom',str(elf),str(hexfile)])
        return {'hex':hexfile.read_text(),'bytes':elf.stat().st_size,'target':'ATmega328P / 16 MHz','libraries':[p.name for p in chosen],'sourceSha256':hashlib.sha256(source.encode()).hexdigest()}
