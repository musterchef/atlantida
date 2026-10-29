"""Autorizzazione interattiva Strava tramite callback sul solo loopback."""
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

from desnivel.trip.strava import request_json


def validate_callback(path, state):
    """Valida destinazione, stato e permesso prima dello scambio del codice."""
    parsed = urlsplit(path)
    query = parse_qs(parsed.query)
    if parsed.path != '/callback' or query.get('state') != [state]:
        raise ValueError('callback non valida: percorso o stato differente')
    if 'error' in query:
        raise ValueError('autorizzazione Strava rifiutata')
    scopes = set(query.get('scope', [''])[0].replace(' ', ',').split(','))
    if 'activity:read_all' not in scopes:
        raise ValueError('permesso activity:read_all non concesso')
    code = query.get('code', [])
    if len(code) != 1 or not code[0]:
        raise ValueError('codice di autorizzazione mancante')
    return code[0]


def authorize(client_id, client_secret, *, timeout_s=300):
    """Mostra il link e attende il browser. Nessuna credenziale viene salvata."""
    state = secrets.token_urlsafe(32)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # L'URL di callback contiene il codice temporaneo.

        def do_GET(self):
            try:
                code = validate_callback(self.path, state)
            except ValueError as error:
                valid_state = parse_qs(urlsplit(self.path).query).get('state') == [state]
                if valid_state and urlsplit(self.path).path == '/callback':
                    result['error'] = str(error)
                self.send_response(400)
                body = 'Autorizzazione non riuscita. Controlla il terminale.'
            else:
                result['code'] = code
                self.send_response(200)
                body = 'Autorizzazione ricevuta. Puoi tornare al terminale.'
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))

    with HTTPServer(('127.0.0.1', 0), Callback) as server:
        server.timeout = 1
        redirect = f'http://127.0.0.1:{server.server_port}/callback'
        query = urlencode(dict(client_id=client_id, redirect_uri=redirect, response_type='code',
                               approval_prompt='force', scope='activity:read_all', state=state))
        print('Apri questo link nel browser e autorizza la sola lettura delle attività:')
        print(f'https://www.strava.com/oauth/authorize?{query}', flush=True)
        deadline = time.monotonic()+timeout_s
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result:
        raise ValueError('nessuna autorizzazione ricevuta entro 5 minuti; rilanciare il comando')
    if 'error' in result:
        raise ValueError(result['error'])
    response = request_json('https://www.strava.com/oauth/token', form=dict(
        client_id=client_id, client_secret=client_secret, code=result['code'], grant_type='authorization_code'))
    token = response.get('access_token')
    if not isinstance(token, str) or not token:
        raise ValueError('Strava non ha restituito un access token valido')
    return token
