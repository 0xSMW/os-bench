import json,sqlite3,tempfile,pathlib
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'db.sqlite'; c=sqlite3.connect(p)
 c.execute('create table t(k text primary key,v integer)'); c.executemany('insert into t values (?,?)',[('a',1),('b',2)]); c.commit()
 value=c.execute('select sum(v) from t').fetchone()[0]; c.close()
 print(json.dumps({'workload':'sqlite','status':'ok' if value==3 else 'error','value':value},sort_keys=True))
