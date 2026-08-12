#include <unistd.h>
static const char msg[]="{\"workload\":\"static_elf\",\"status\":\"ok\"}\n";
int main(void){return write(1,msg,sizeof(msg)-1)==(ssize_t)(sizeof(msg)-1)?0:1;}
