from __future__ import annotations
from pathlib import Path
import pytest
from osbench.qemu import QemuController,load_profile

def test_profiles_load(): assert load_profile('macos_tcg').accelerator=='tcg'; assert load_profile('linux_kvm').accelerator=='kvm'

def test_unknown_profile():
 with pytest.raises(KeyError): load_profile('missing')

def test_command_construction(monkeypatch,tmp_path):
 code=tmp_path/'code.fd';code.write_bytes(b'x');vars=tmp_path/'vars.fd';vars.write_bytes(b'x');image=tmp_path/'disk.qcow2';image.write_bytes(b'x')
 controller=QemuController('macos_tcg')
 object.__setattr__(controller.profile,'firmware_code_candidates',[str(code)])
 cmd=controller.build_command(image=image,serial_path=tmp_path/'serial',qmp_path=tmp_path/'qmp',vars_path=vars,auxiliary_media=[])
 assert '-qmp' in cmd and str(image) in ' '.join(cmd)
