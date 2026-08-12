#!/usr/bin/env python3
import socket, threading
listener=socket.socket();listener.bind(("127.0.0.1",0));listener.listen(1);port=listener.getsockname()[1]
def serve():
    conn,_=listener.accept();data=conn.recv(16);conn.sendall(data[::-1]);conn.close()
thread=threading.Thread(target=serve);thread.start()
client=socket.create_connection(("127.0.0.1",port),timeout=5);client.sendall(b"osbench");assert client.recv(16)==b"hcnebso";client.close();thread.join();listener.close();print("tcp-loopback-ok")
