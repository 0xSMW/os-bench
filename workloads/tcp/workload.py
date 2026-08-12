import json,socket,threading
s=socket.socket();s.bind(('127.0.0.1',0));s.listen(1)
def server():
 c,_=s.accept(); data=c.recv(64); c.sendall(data[::-1]);c.close()
t=threading.Thread(target=server);t.start();c=socket.create_connection(s.getsockname(),timeout=2);c.sendall(b'osbench');reply=c.recv(64);c.close();t.join();s.close()
print(json.dumps({'workload':'tcp','status':'ok' if reply==b'hcnebso' else 'error','reply':reply.decode()},sort_keys=True))
