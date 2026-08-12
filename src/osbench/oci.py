from __future__ import annotations
import hashlib,json,tarfile,tempfile
from pathlib import Path
from .util import sha256_file,stable_json,write_json

def build_oci_layout(rootfs_tar:Path,*,output_dir:Path,archive_path:Path|None=None)->dict:
    output_dir.mkdir(parents=True,exist_ok=True);blobs=output_dir/'blobs/sha256';blobs.mkdir(parents=True,exist_ok=True)
    layer_digest=sha256_file(rootfs_tar);layer=blobs/layer_digest
    if not layer.exists():layer.write_bytes(Path(rootfs_tar).read_bytes())
    config={"architecture":"amd64","os":"linux","rootfs":{"type":"layers","diff_ids":[f"sha256:{layer_digest}"]},"config":{},"history":[{"created_by":"OSBench reference export"}]}
    cb=stable_json(config).encode();cd=hashlib.sha256(cb).hexdigest();(blobs/cd).write_bytes(cb)
    manifest={"schemaVersion":2,"mediaType":"application/vnd.oci.image.manifest.v1+json","config":{"mediaType":"application/vnd.oci.image.config.v1+json","digest":f"sha256:{cd}","size":len(cb)},"layers":[{"mediaType":"application/vnd.oci.image.layer.v1.tar","digest":f"sha256:{layer_digest}","size":Path(rootfs_tar).stat().st_size}]}
    mb=stable_json(manifest).encode();md=hashlib.sha256(mb).hexdigest();(blobs/md).write_bytes(mb)
    index={"schemaVersion":2,"manifests":[{"mediaType":"application/vnd.oci.image.manifest.v1+json","digest":f"sha256:{md}","size":len(mb),"annotations":{"org.opencontainers.image.ref.name":"13.6-v0.1"}}]}
    write_json(output_dir/'index.json',index);write_json(output_dir/'oci-layout',{"imageLayoutVersion":"1.0.0"});write_json(output_dir/'osbench-manifest.json',{"layer":layer_digest,"config":cd,"manifest":md})
    if archive_path:
        with tarfile.open(archive_path,'w') as tar:
            for p in sorted(output_dir.rglob('*')):tar.add(p,arcname=p.relative_to(output_dir))
    return {"layout":str(output_dir),"archive":str(archive_path) if archive_path else None,"manifest_digest":md,"rootfs_digest":layer_digest}
