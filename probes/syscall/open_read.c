#include "../runtime/raw_syscall.h"
void _start(void) { char b[16]; long fd=sc4(SYS_openat,AT_FDCWD,(long)"/etc/os-release",O_RDONLY,0); if(fd<0) fail("open_read"); long n=sc3(SYS_read,fd,(long)b,sizeof(b)); sc1(SYS_close,fd); if(n<=0) fail("open_read"); ok("open_read"); }
