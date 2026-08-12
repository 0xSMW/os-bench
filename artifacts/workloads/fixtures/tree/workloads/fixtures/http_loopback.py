#!/usr/bin/env python3
import http.server, threading, urllib.request
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),http.server.SimpleHTTPRequestHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/",timeout=5) as response:
    assert response.status==200
server.shutdown();thread.join(timeout=5);server.server_close();print("http-loopback-ok")
