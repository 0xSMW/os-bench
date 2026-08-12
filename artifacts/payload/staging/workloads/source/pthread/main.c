#include <pthread.h>
#include <stdio.h>
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER; static long value;
static void *worker(void *p){long n=(long)p;for(long i=0;i<n;i++){pthread_mutex_lock(&lock);value++;pthread_mutex_unlock(&lock);}return 0;}
int main(void){pthread_t a,b;pthread_create(&a,0,worker,(void*)10000);pthread_create(&b,0,worker,(void*)10000);pthread_join(a,0);pthread_join(b,0);printf("{\"workload\":\"pthread\",\"status\":\"%s\",\"value\":%ld}\n",value==20000?"ok":"error",value);return value==20000?0:1;}
