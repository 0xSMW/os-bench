#!/usr/bin/env python3
import json,socket,threading
s=socket.socket();s.bind(("127.0.0.1",0));s.listen(1);port=s.getsockname()[1]
def client():
 c=socket.create_connection(("127.0.0.1",port));c.sendall(b"ping");c.close()
t=threading.Thread(target=client);t.start();c,_=s.accept();data=c.recv(4);c.close();s.close();t.join();print(json.dumps({"status":"ok","payload":data.decode()}))
