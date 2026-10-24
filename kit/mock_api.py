"""mock_api.py <demo_dir> [port]: serve a recorded demo panel API (see demo/<product>/api.json)."""
import json, os, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIR = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
STORE = json.load(open(os.path.join(DIR, 'api.json')))
DROP = {'page', 'per_page', 'limit'}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype='application/json'):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        if u.path.startswith('/storage/'):
            f = os.path.join(DIR, 'files', u.path.lstrip('/'))
            if os.path.isfile(f):
                return self.send(200, open(f, 'rb').read(), 'application/pdf' if f.endswith('.pdf') else 'application/octet-stream')
            return self.send(404, '{}')
        path = u.path.removeprefix('/api/v1/').strip('/')
        params = dict(urllib.parse.parse_qsl(u.query))
        q = sorted((k, v) for k, v in params.items() if k not in DROP)
        body = STORE.get(path + ('?' + urllib.parse.urlencode(q) if q else '')) or STORE.get(path)
        if body is None:
            print('miss', self.path, flush=True)
            return self.send(200, '{"data":[],"meta":{"current_page":1,"last_page":1,"total":0}}' if '/' not in path else '{}')
        page = int(params.get('page', '1') or 1)
        if page > 1:  # everything was recorded on page 1
            d = json.loads(body)
            if isinstance(d, dict) and 'data' in d:
                d['data'] = []
                d.setdefault('meta', {})['current_page'] = page
                if 'links' in d:
                    d['links']['next'] = None
                body = json.dumps(d)
        self.send(200, body)

    def do_POST(self):
        self.send(200, '{"ok":true}')


ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
