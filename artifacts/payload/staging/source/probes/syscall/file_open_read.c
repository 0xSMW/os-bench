#include "../runtime/raw_syscall.h"
void _start(void){ const char p[]="/etc/os-release"; char b[8]; long f=osb_syscall4(OSB_SYS_openat,OSB_AT_FDCWD,(long)p,OSB_O_RDONLY,0); long n=f>=0?osb_syscall3(OSB_SYS_read,f,(long)b,8):-1; if(f>=0)osb_syscall1(OSB_SYS_close,f); osb_result("file_open_read",f>=0&&n>0); }
