"""Loopback-only local application server. No third-party Python dependencies."""
import argparse
import base64
import binascii
import json
import re
import subprocess
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from circuit import simulate
from boards.service import run_board, compile_sketch, board_catalogue
from boards.fritzing_parts import import_part, list_parts, svg_path
from boards.protocols import decode_capture
from boards import arduino_cli
from boards.project_service import run_project, capabilities
from boards.libraries import install_library, list_libraries
from boards.verification import example_hex, example_sketches, verify_models

ROOT=Path(__file__).parent/'web'
SLOTS=threading.BoundedSemaphore(2)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
        super().end_headers()
    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.valid_host():self.reply(403,{'error':'Invalid local host.'});return
        if self.path=='/api/boards/examples':
            try:self.reply(200,example_hex())
            except OSError:self.reply(503,{'error':'Bundled firmware examples are missing.'})
            return
        if self.path=='/api/projects/capabilities':self.reply(200,capabilities());return
        if self.path=='/api/boards/sketches':self.reply(200,example_sketches());return
        if self.path=='/api/boards':self.reply(200,{'boards':board_catalogue()});return
        if self.path=='/api/visual-parts':self.reply(200,{'parts':list_parts()});return
        match=re.fullmatch(r'/api/visual-parts/([0-9a-f]{32})\.svg',self.path)
        if match:
            try:body=svg_path(match.group(1)).read_bytes()
            except (ValueError,FileNotFoundError):self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type','image/svg+xml');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        if self.path=='/api/arduino-cli/status':self.reply(200,arduino_cli.status());return
        if self.path=='/api/arduino-cli/libraries':self.reply(200,arduino_cli.list_libraries());return
        if self.path=='/api/libraries':self.reply(200,{'libraries':list_libraries()});return
        asset=self.path.split('?')[0]
        if re.fullmatch(r'/vendor/components/(?:catalog\.json|(?:art/[a-z]+-[0-9a-f]{16}\.svg)|(?:notices/[a-z]+\.txt))',asset):
            target=ROOT/asset.lstrip('/')
            if target.is_file() and target.resolve()==target.absolute():
                super().do_GET();return
            self.send_error(404);return
        if asset.startswith('/vendor/') and asset in {'/vendor/'+p.name for p in (ROOT/'vendor').glob('*') if p.suffix in {'.js','.json','.txt'}}:
            super().do_GET();return
        if asset.startswith('/parts/') and asset in {'/parts/'+p.name for p in (ROOT/'parts').glob('*') if p.suffix in {'.svg','.json'}}:
            super().do_GET();return
        if self.path.split('?')[0] not in {'/','/index.html','/style.css','/app.js','/favicon.svg','/boards.html','/boards.css','/boards.js','/parts-ui.js','/parts.css','/integrations.js','/component-library.js','/lab.html','/lab.js','/lab.css','/practical-examples.json'}:
            self.send_error(404);return
        super().do_GET()
    def do_POST(self):
        if not self.valid_host():self.reply(403,{'error':'Invalid local host.'});return
        origin=self.headers.get('Origin')
        expected=f'http://{self.headers.get("Host", "")}'
        if origin and origin!=expected:
            self.reply(403,{'error':'Cross-origin requests are not allowed.'});return
        if self.path not in {'/api/projects/run','/api/simulate','/api/boards/run','/api/boards/compile','/api/libraries/install','/api/boards/verify','/api/arduino-cli/search','/api/arduino-cli/install','/api/boards/decode','/api/visual-parts/import'}:self.reply(404,{'error':'Unknown operation.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=(1500000 if self.path in {'/api/libraries/install','/api/boards/decode','/api/visual-parts/import'} else 300000):raise ValueError('Project exceeds the request limit.')
            if not SLOTS.acquire(blocking=False):
                self.reply(429,{'error':'Simulation is busy. Try again shortly.'});return
            try:
                config=json.loads(self.rfile.read(size))
                if self.path=='/api/visual-parts/import':
                    try:packed=base64.b64decode(config.get('archive',''),validate=True)
                    except (binascii.Error,TypeError):raise ValueError('Invalid Fritzing archive')
                    result=import_part(packed)
                elif self.path=='/api/boards/decode':result=decode_capture(config)
                elif self.path=='/api/arduino-cli/search':result=arduino_cli.search_libraries(config.get('query'))
                elif self.path=='/api/arduino-cli/install':result=arduino_cli.install_library(config.get('name'),config.get('version'))
                elif self.path=='/api/projects/run':result=run_project(config)
                elif self.path=='/api/simulate':result=simulate(config)
                elif self.path=='/api/boards/verify':result=verify_models()
                elif self.path=='/api/boards/run':result=run_board(config)
                elif self.path=='/api/boards/compile':result=compile_sketch(config.get('source'),board=config.get('board','arduino-uno'))
                else:
                    try:packed=base64.b64decode(config.get('archive',''),validate=True)
                    except (binascii.Error,TypeError):raise ValueError('Invalid ZIP upload.')
                    result=install_library(packed)
            finally:SLOTS.release()
            self.reply(200,result)
        except (ValueError,TypeError,KeyError,AttributeError) as exc:self.reply(400,{'error':str(exc)})
        except (RuntimeError,FileNotFoundError) as exc:self.reply(503,{'error':str(exc)})
        except subprocess.TimeoutExpired:self.reply(408,{'error':'Operation exceeded its time limit. Simplify the circuit or firmware and try again.'})
    def reply(self,status,data):
        body=json.dumps(data,allow_nan=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    print(f'Mina circuit workbench: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
