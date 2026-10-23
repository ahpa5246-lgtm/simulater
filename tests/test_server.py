import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from server import Handler
from test_circuit import divider

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path='/',body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=20)
        connection.request('POST' if body is not None else 'GET',path,body,headers or {})
        response=connection.getresponse();data=response.read();connection.close();return response.status,data
    def test_practical_workspace_routes_and_early_validation(self):
        self.assertEqual(self.request('/lab.html')[0],200)
        self.assertEqual(self.request('/lab.js')[0],200)
        status,body=self.request('/api/projects/capabilities')
        self.assertEqual(status,200);self.assertEqual(len(json.loads(body)['records']),363)
        status,body=self.request('/api/projects/run',json.dumps({'project':{'version':1,'board':'esp32','components':[]},'source':'invalid source'}),{'Content-Type':'application/json'})
        self.assertEqual(status,400);self.assertIn(b'Uno',body)

    def test_serves_application(self):
        status,data=self.request();self.assertEqual(status,200);self.assertIn(b'Circuit Workbench',data)
    def test_serves_component_library_and_blocks_traversal(self):
        self.assertEqual(self.request('/component-library.js')[0],200)
        status,body=self.request('/vendor/components/catalog.json')
        self.assertEqual(status,200)
        part=json.loads(body)['parts'][0]
        self.assertEqual(self.request(part['svgUrl'])[0],200)
        self.assertEqual(self.request(part['noticeUrl'])[0],200)
        for path in ['/vendor/components/art/../../../../server.py','/vendor/components/art/%2e%2e/server.py','/vendor/components/notices/../catalog.json','/vendor/components/']:
            self.assertEqual(self.request(path)[0],404)

    def test_bundled_firmware_can_run_without_compilation(self):
        status,data=self.request('/api/boards/examples')
        self.assertEqual(status,200)
        firmware=json.loads(data)['analog']
        status,data=self.request('/api/boards/run',json.dumps({'board':'arduino-uno','hex':firmware,'durationMs':60,'sensors':[{'model':'lm35','value':25,'pin':0}]}),{'Content-Type':'application/json'})
        self.assertEqual(status,200);self.assertIn('ADC: 51',json.loads(data)['serial'])

    def test_simulates_through_api(self):
        status,data=self.request('/api/simulate',json.dumps(divider()),{'Content-Type':'application/json'})
        self.assertEqual(status,200);self.assertAlmostEqual(json.loads(data)['dc']['out'],5)
    def test_rejects_foreign_origin(self):
        status,_=self.request('/api/simulate','{}',{'Origin':'https://evil.example'})
        self.assertEqual(status,403)
    def test_rejects_foreign_host(self):
        status,_=self.request('/api/simulate',json.dumps(divider()),{'Host':'evil.example','Origin':'http://evil.example'})
        self.assertEqual(status,403)
    def test_blocks_private_source_files(self):
        self.assertEqual(self.request('/../circuit.py')[0],404)
    def test_returns_error_for_bad_project(self):
        self.assertEqual(self.request('/api/simulate','{}')[0],400)

if __name__=='__main__':unittest.main()
