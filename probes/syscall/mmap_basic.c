#include "../runtime/raw_syscall.h"
void _start(void){ long p=osb_syscall6(OSB_SYS_mmap,0,4096,OSB_PROT_READ|OSB_PROT_WRITE,OSB_MAP_PRIVATE|OSB_MAP_ANONYMOUS,-1,0); int ok=p>0; if(ok){((volatile char*)p)[0]='x';ok=((volatile char*)p)[0]=='x';osb_syscall2(OSB_SYS_munmap,p,4096);} osb_result("mmap_basic",ok); }
