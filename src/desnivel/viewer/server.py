"""Server HTTP locale: risorse della vista, geometria e snapshot su file."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
import os
from pathlib import Path
from threading import Thread
import time
from urllib.parse import urlsplit

from desnivel.viewer.route import route_payload


class JourneyViewServer:
    """Il thread HTTP legge solo il file di stato, senza accedere al runtime."""

    def __init__(self, track, status_path, port):
        route = json.dumps(route_payload(track), allow_nan=False).encode('utf-8')
        status_path = Path(status_path)
        assets = files('desnivel.viewer')
        resources = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/view.css': ('view.css', 'text/css; charset=utf-8'),
                     '/view.js': ('view.js', 'text/javascript; charset=utf-8'),
                     '/position.js': ('position.js', 'text/javascript; charset=utf-8')}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                if path == '/api/route':
                    self.respond(200, route, 'application/json')
                elif path == '/api/state':
                    try:
                        # fstat sul file aperto: età e contenuto dello stesso snapshot atomico.
                        with status_path.open(encoding='utf-8') as stream:
                            state = json.load(stream)
                            age = max(0., time.time()-os.fstat(stream.fileno()).st_mtime)
                        body = json.dumps({'age_s': age, 'session': state}, allow_nan=False).encode('utf-8')
                    except (OSError, ValueError) as error:
                        body = json.dumps({'error': f'Stato non disponibile: {error}'}).encode('utf-8')
                        self.respond(503, body, 'application/json')
                        return
                    self.respond(200, body, 'application/json')
                elif path in resources:
                    filename, content_type = resources[path]
                    self.respond(200, assets.joinpath(filename).read_bytes(), content_type)
                else:
                    self.respond(404, b'Not found', 'text/plain')

            def respond(self, status, body, content_type):
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # Il browser ha chiuso la richiesta.

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.thread = Thread(target=self.server.serve_forever, name='journey-view', daemon=True)

    @property
    def url(self):
        return f'http://127.0.0.1:{self.server.server_port}/'

    def start(self):
        self.thread.start()

    def close(self):
        if self.thread.is_alive():
            self.server.shutdown()
            self.thread.join()
        self.server.server_close()
