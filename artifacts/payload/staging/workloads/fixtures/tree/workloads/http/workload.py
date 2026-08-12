import http.server,json,socketserver,threading,urllib.request
class H(http.server.BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'osbench')
 def log_message(self,*a): pass
with socketserver.TCPServer(('127.0.0.1',0),H) as s:
 t=threading.Thread(target=s.handle_request);t.start(); body=urllib.request.urlopen(f'http://127.0.0.1:{s.server_address[1]}/',timeout=2).read();t.join()
print(json.dumps({'workload':'http','status':'ok' if body==b'osbench' else 'error','bytes':len(body)},sort_keys=True))
