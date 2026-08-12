CC ?= x86_64-linux-gnu-gcc
OUT ?= ../artifacts/probes
CFLAGS := -Os -static -nostdlib -nostartfiles -nodefaultlibs -fno-stack-protector -fno-builtin -fno-asynchronous-unwind-tables -fno-pie -no-pie -Wall -Wextra -Werror
SOURCES := syscall/write_exit.c syscall/open_read.c syscall/stat.c syscall/mmap.c syscall/fork_wait.c syscall/pipe.c syscall/socket.c syscall/futex.c syscall/clock.c syscall/invalid_fd.c
BINS := $(patsubst syscall/%.c,$(OUT)/%,$(SOURCES))

all: $(BINS)

$(OUT)/%: syscall/%.c runtime/raw_syscall.h
	@mkdir -p $(OUT)
	$(CC) $(CFLAGS) -I runtime $< -o $@
	strip $@ 2>/dev/null || true

clean:
	rm -rf $(OUT)
