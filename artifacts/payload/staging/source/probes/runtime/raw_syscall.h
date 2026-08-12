#ifndef OSBENCH_RAW_SYSCALL_H
#define OSBENCH_RAW_SYSCALL_H

typedef unsigned long usize;
typedef long isize;

static inline long sc0(long n) {
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n) : "rcx", "r11", "memory"); return r;
}
static inline long sc1(long n, long a) {
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a) : "rcx", "r11", "memory"); return r;
}
static inline long sc2(long n, long a, long b) {
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b) : "rcx", "r11", "memory"); return r;
}
static inline long sc3(long n, long a, long b, long c) {
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory"); return r;
}
static inline long sc4(long n, long a, long b, long c, long d) {
    register long r10 __asm__("r10") = d;
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10) : "rcx", "r11", "memory"); return r;
}
static inline long sc5(long n, long a, long b, long c, long d, long e) {
    register long r10 __asm__("r10") = d; register long r8 __asm__("r8") = e;
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8) : "rcx", "r11", "memory"); return r;
}
static inline long sc6(long n, long a, long b, long c, long d, long e, long f) {
    register long r10 __asm__("r10") = d; register long r8 __asm__("r8") = e; register long r9 __asm__("r9") = f;
    long r; __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8), "r"(r9) : "rcx", "r11", "memory"); return r;
}

#define SYS_read 0
#define SYS_write 1
#define SYS_close 3
#define SYS_fstat 5
#define SYS_poll 7
#define SYS_mmap 9
#define SYS_munmap 11
#define SYS_pipe 22
#define SYS_nanosleep 35
#define SYS_getpid 39
#define SYS_socket 41
#define SYS_connect 42
#define SYS_accept 43
#define SYS_bind 49
#define SYS_listen 50
#define SYS_fork 57
#define SYS_wait4 61
#define SYS_futex 202
#define SYS_clock_gettime 228
#define SYS_openat 257
#define SYS_newfstatat 262
#define SYS_exit 60

#define AT_FDCWD -100
#define O_RDONLY 0
#define O_CREAT 0100
#define O_TRUNC 01000
#define O_RDWR 02
#define PROT_READ 1
#define PROT_WRITE 2
#define MAP_PRIVATE 2
#define MAP_ANONYMOUS 0x20
#define AF_INET 2
#define SOCK_STREAM 1
#define FUTEX_WAIT 0
#define FUTEX_WAKE 1

static usize cstrlen(const char *s) { usize n = 0; while (s[n]) n++; return n; }
static void emit(const char *s) { sc3(SYS_write, 1, (long)s, (long)cstrlen(s)); }
static void finish(int code) { sc1(SYS_exit, code); __builtin_unreachable(); }
static void ok(const char *name) {
    emit("{\"status\":\"ok\",\"probe\":\""); emit(name); emit("\"}\n"); finish(0);
}
static void fail(const char *name) {
    emit("{\"status\":\"error\",\"probe\":\""); emit(name); emit("\"}\n"); finish(1);
}

#endif
