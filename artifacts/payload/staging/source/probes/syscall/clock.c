#include "../runtime/raw_syscall.h"
struct timespec { long sec; long nsec; };
void _start(void) { struct timespec a,b,req={0,1000000}; if(sc2(SYS_clock_gettime,1,(long)&a)<0) fail("clock"); sc2(SYS_nanosleep,(long)&req,0); if(sc2(SYS_clock_gettime,1,(long)&b)<0) fail("clock"); if(b.sec<a.sec || (b.sec==a.sec && b.nsec<a.nsec)) fail("clock"); ok("clock"); }
