"""demo_sources.py <wallpapers_dir> [port]: a demo WordPress site, Blogger blog and Google Drive folder
for the wallpaper-source apps, all serving the images in <wallpapers_dir>/<category>/*.jpg."""
import json, os, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIR = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
HOME = f'http://127.0.0.1:{PORT}'
CATS = sorted(c for c in os.listdir(DIR) if os.path.isdir(os.path.join(DIR, c)))
IMAGES = []  # (id, category, file)
for ci, c in enumerate(CATS):
    for f in sorted(os.listdir(os.path.join(DIR, c))):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            IMAGES.append((len(IMAGES) + 1, c, f))
# newest first, categories interleaved so "Latest" shows a mix
IMAGES.sort(key=lambda x: (int(''.join(ch for ch in x[2] if ch.isdigit()) or 0), x[1]))
DATES = {img[0]: f'2026-10-{20 - min(i // 3, 19):02d}T{10 + i % 9:02d}:00:00' for i, img in enumerate(IMAGES)}
url = lambda c, f: f'{HOME}/img/{c}/{f}'
title = lambda c, f: f'{c.title()} {int("".join(ch for ch in f if ch.isdigit()) or 0)}'


def wp_posts(params):
    cat = params.get('categories')
    out = []
    for i, c, f in IMAGES:
        cid = CATS.index(c) + 1
        if cat and str(cid) not in cat.split(','):
            continue
        u = url(c, f)
        out.append({'id': i, 'date': DATES[i], 'date_gmt': DATES[i], 'link': f'{HOME}/?p={i}', 'title': {'rendered': title(c, f)},
                    'categories': [cid], '_embedded': {'author': [{'name': 'Demo'}], 'wp:term': [[{'taxonomy': 'category', 'name': c.title()}]],
                    'wp:featuredmedia': [{'source_url': u, 'mime_type': 'image/jpeg', 'media_details': {'width': 1080, 'height': 2340,
                    'sizes': {'full': {'source_url': u}, 'medium': {'source_url': u}, 'large': {'source_url': u}}}}]}})
    return out


def blogger_feed(label, start, size):
    entries = []
    for i, c, f in IMAGES:
        if label and c.lower() != label.lower():
            continue
        u = url(c, f)
        entries.append({'id': {'$t': f'tag:blogger.com,1999:blog-1000000.post-{i}'}, 'title': {'$t': title(c, f)},
                        'content': {'$t': f'<a href="{u}"><img src="{u}" data-original-width="1080" data-original-height="2340" width="320"></a>'},
                        'published': {'$t': DATES[i] + '.000+00:00'}, 'updated': {'$t': DATES[i] + '.000+00:00'},
                        'link': [{'rel': 'alternate', 'href': f'{HOME}/{i}.html'}], 'category': [{'term': c.title()}],
                        'author': [{'name': {'$t': 'Demo'}}]})
    total = len(entries)
    return {'feed': {'category': [{'term': c.title()} for c in CATS], 'openSearch$totalResults': {'$t': str(total)},
                     'entry': entries[start - 1:start - 1 + size]}}


def drive_list(folder):
    if not folder.startswith('cat-'):
        return [{'id': f'cat-{c}', 'name': c.title(), 'mimeType': 'application/vnd.google-apps.folder'} for c in CATS]
    c = folder.removeprefix('cat-')
    return [{'id': f'img-{i}', 'name': f, 'mimeType': 'image/jpeg', 'createdTime': DATES[i] + 'Z', 'size': '300000',
             'imageMediaMetadata': {'width': 1080, 'height': 2340}} for i, cc, f in IMAGES if cc == c]


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype='application/json', headers=None):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def image(self, c, f):
        return self.send(200, open(os.path.join(DIR, c, f), 'rb').read(), 'image/jpeg')

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        p = dict(urllib.parse.parse_qsl(u.query))
        path = u.path
        if path.startswith('/img/'):
            _, _, c, f = path.split('/', 3)
            return self.image(c, urllib.parse.unquote(f))
        if path.startswith('/wp-json/wp/v2/categories'):
            cats = [{'id': i + 1, 'name': c.title(), 'slug': c, 'count': sum(1 for x in IMAGES if x[1] == c), 'parent': 0} for i, c in enumerate(CATS)]
            return self.send(200, cats if p.get('page', '1') == '1' else [], headers={'X-WP-TotalPages': '1', 'X-WP-Total': str(len(cats))})
        if path.startswith('/wp-json/wp/v2/'):
            posts = wp_posts(p) if p.get('page', '1') == '1' else []
            return self.send(200, posts, headers={'X-WP-TotalPages': '1', 'X-WP-Total': str(len(posts))})
        if path.startswith('/feeds/posts/default'):
            label = urllib.parse.unquote(path.split('/-/', 1)[1]) if '/-/' in path else None
            return self.send(200, blogger_feed(label, int(p.get('start-index', 1)), int(p.get('max-results', 150))))
        if path == '/drive/v3/files':
            folder = p.get('q', '').split("'")[1] if "'" in p.get('q', '') else 'demo'
            return self.send(200, {'files': drive_list(folder)})
        if path.startswith('/drive/v3/files/img-') or path == '/thumbnail' or path == '/uc':
            fid = path.rsplit('/', 1)[-1] if path.startswith('/drive') else p.get('id', '')
            i = int(fid.removeprefix('img-') or 0)
            hit = next((x for x in IMAGES if x[0] == i), None)
            return self.image(hit[1], hit[2]) if hit else self.send(404, '{}')
        print('miss', self.path, flush=True)
        self.send(200, '<html><body>Demo</body></html>', 'text/html')


ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
