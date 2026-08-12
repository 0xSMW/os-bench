import json,socket
records=socket.getaddrinfo('localhost',None)
print(json.dumps({'workload':'dns','status':'ok' if records else 'error','records':len(records)},sort_keys=True))
