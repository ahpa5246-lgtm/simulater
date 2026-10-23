"""Loopback-only local application server. No third-party Python dependencies."""
import argparse
import base64
import binascii
import json
import subprocess
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from circuit import simulate
from boards.service import run_board, compile_sketch, board_catalogue
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
        if self.path=='/api/boards/sketches':self.reply(200,example_sketches());return
        if self.path=='/api/boards':self.reply(200,{'boards':board_catalogue()});return
        if self.path=='/api/libraries':self.reply(200,{'libraries':list_libraries()});return
        asset=self.path.split('?')[0]
        if asset.startswith('/parts/') and asset in {'/parts/'+p.name for p in (ROOT/'parts').glob('*') if p.suffix in {'.svg','.json'}}:
            super().do_GET();return
        if self.path.split('?')[0] not in {'/','/index.html','/style.css','/app.js','/favicon.svg','/boards.html','/boards.css','/boards.js','/parts-ui.js','/parts.css'}:
            self.send_error(404);return
        super().do_GET()
    def do_POST(self):
        if not self.valid_host():self.reply(403,{'error':'Invalid local host.'});return
        origin=self.headers.get('Origin')
        expected=f'http://{self.headers.get("Host", "")}'
        if origin and origin!=expected:
            self.reply(403,{'error':'Cross-origin requests are not allowed.'});return
        if self.path not in {'/api/simulate','/api/boards/run','/api/boards/compile','/api/libraries/install','/api/boards/verify'}:self.reply(404,{'error':'Unknown operation.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=(1500000 if self.path=='/api/libraries/install' else 300000):raise ValueError('Project exceeds the request limit.')
            if not SLOTS.acquire(blocking=False):
                self.reply(429,{'error':'Simulation is busy. Try again shortly.'});return
            try:
                config=json.loads(self.rfile.read(size))
                if self.path=='/api/simulate':result=simulate(config)
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
