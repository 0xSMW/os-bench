# Multi-architecture immutable Debian 13.6 base. Docker selects the host architecture.
FROM debian:13.6-slim@sha256:020c0d20b9880058cbe785a9db107156c3c75c2ac944a6aa7ab59f2add76a7bd

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    cpio \
    curl \
    dosfstools \
    e2fsprogs \
    file \
    gcc \
    gcc-x86-64-linux-gnu \
    libc6-dev-amd64-cross \
    git \
    gnupg \
    iproute2 \
    iputils-ping \
    jq \
    libguestfs-tools \
    make \
    mtools \
    openssh-client \
    ovmf \
    parted \
    procps \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-venv \
    qemu-system-x86 \
    qemu-utils \
    rsync \
    socat \
    sqlite3 \
    strace \
    xorriso \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python3 -m pip install --break-system-packages --no-build-isolation --no-cache-dir '.[dev]'

COPY . .
ENTRYPOINT ["osbench"]
CMD ["--help"]
