#!/usr/bin/env python3
import os,sqlite3,tempfile
fd,path=tempfile.mkstemp();os.close(fd)
try:
 c=sqlite3.connect(path);c.execute('create table t(k primary key,v)');c.execute('insert into t values(?,?)',(1,'ok'));c.commit();assert c.execute('select v from t').fetchone()[0]=='ok';c.close()
finally:os.unlink(path)
print('sqlite-ok')
