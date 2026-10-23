"""Build optional GPL PICSimLab peripheral adapter using local C++ compiler."""
import os, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
output=root/'.tools/picsimlab-ds1621.node';output.parent.mkdir(exist_ok=True)
subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-shared','-fPIC','-O2','-I'+str(root/'node_modules/node-api-headers/include'),str(root/'boards/picsimlab-native.cc'),str(root/'third_party/picsimlab/sen_ds1621.cc'),str(root/'third_party/picsimlab/sen_bmp180.cc'),str(root/'third_party/picsimlab/bitbang_i2c.cc'),'-o',str(output)],check=True)
print(output)
