"""Export a Renode launch script using the bundled upstream STM32F103 platform.

This prepares a local Renode session; it does not enable the browser's pending
STM32 adapter or claim that the firmware has been run/verified.
"""
import argparse,re
from pathlib import Path

def script(firmware):
 firmware=Path(firmware).resolve();header=firmware.read_bytes()[:52]
 if len(header)<52 or header[:7]!=b'\x7fELF\x01\x01\x01' or int.from_bytes(header[18:20],'little')!=40:raise ValueError('Requires a little-endian 32-bit ARM ELF built for STM32F103')
 platform=Path(__file__).resolve().parents[1]/'third_party/renode/platforms/cpus/stm32f103.repl'
 for path in [firmware,platform]:
  if not re.fullmatch(r'[A-Za-z0-9_./:\\-]+',path.as_posix()):raise ValueError('Move firmware/project to a path containing no spaces or command punctuation')
 return f'using sysbus\nmach create\nmachine LoadPlatformDescription @{platform.as_posix()}\nsysbus LoadELF @{firmware.as_posix()}\nstart\n'
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('firmware');p.add_argument('--output',required=True);args=p.parse_args()
 try:Path(args.output).write_text(script(args.firmware));print('Exported STM32F103 Renode script. Run with installed Renode; browser STM32 support remains pending.')
 except (OSError,ValueError) as e:p.exit(1,str(e)+'\n')
