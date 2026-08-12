from __future__ import annotations
import platform,shutil,sys
from pathlib import Path
from .contracts import validate_contracts
from .paths import repo_root

def doctor():
    tools={name:shutil.which(name) for name in ["docker","qemu-system-x86_64","qemu-img","xorriso","guestfish","virt-copy-out","strace","gcc","dpkg-deb"]}
    firmware=[str(p) for p in [Path('/usr/share/OVMF/OVMF_CODE_4M.fd'),Path('/usr/share/OVMF/OVMF_CODE.fd')] if p.exists()]
    report=validate_contracts(); root=repo_root(); image=root/'artifacts/reference/debian-13.6-amd64.qcow2'
    guest=sum(c.get('transport') not in {'host','raw_syscall','shell','none'} for c in report.contracts)
    return {"python":sys.version.split()[0],"platform":platform.platform(),"machine":platform.machine(),"root":str(root),"tools":tools,"firmware":firmware,"reference_image":str(image),"reference_image_exists":image.exists(),"contracts":len(report.contracts),"contract_issues":[i.__dict__ for i in report.issues],"host_mapped":len(report.contracts)-guest,"guest_only":guest}
