"""Local inventory reference endpoint; never contacts an external SAP system."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import contextmanager


@contextmanager
def reference_service(healthy=False):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=json.dumps({'status':'ok' if healthy else 'unavailable',
                             'fixture':True,'inventory_available':healthy}).encode()
            self.send_response(200 if healthy else 503)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}/inventory'
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
