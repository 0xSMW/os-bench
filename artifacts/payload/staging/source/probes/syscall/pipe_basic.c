#include "../runtime/raw_syscall.h"
void _start(void){ int f[2]={-1,-1}; char b=0; long r=osb_syscall1(OSB_SYS_pipe,(long)f); long w=r==0?osb_syscall3(OSB_SYS_write,f[1],(long)"p",1):-1; long n=r==0?osb_syscall3(OSB_SYS_read,f[0],(long)&b,1):-1; if(r==0){osb_syscall1(OSB_SYS_close,f[0]);osb_syscall1(OSB_SYS_close,f[1]);} osb_result("pipe_basic",r==0&&w==1&&n==1&&b=='p'); }
