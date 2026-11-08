"""Build a static nasm binary once on the CI host.

On the x86_64 Linux runner, cibuildwheel builds both manylinux and musllinux
in separate containers. Without this, each container would build nasm from
source. A statically linked nasm runs under both glibc and musl, so we build it
here and put it on the containers' PATH (see the workflow). build-ffmpeg.py then
uses it, because it reports the version pinned in pkg.py.
"""

import argparse
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile

from pkg import nasm_package


def main() -> None:
    parser = argparse.ArgumentParser("build-nasm")
    parser.add_argument("destination", help="directory to put the nasm binary in")
    args = parser.parse_args()

    dest_dir = os.path.abspath(args.destination)
    tarball = os.path.abspath(
        os.path.join("source", nasm_package.source_url.split("/")[-1])
    )

    env = os.environ.copy()
    if platform.system() == "Linux":
        env["LDFLAGS"] = "-static"

    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(tarball) as tar:
            tar.extractall(tmp, filter="data")
        (src_dir,) = [os.path.join(tmp, name) for name in os.listdir(tmp)]

        # --without-zlib uses nasm's bundled zlib, so no system libz.a is needed
        subprocess.run(
            ["./configure", "--without-zlib"], cwd=src_dir, env=env, check=True
        )
        subprocess.run(
            ["make", f"-j{os.cpu_count()}", "nasm"], cwd=src_dir, env=env, check=True
        )

        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(os.path.join(src_dir, "nasm"), os.path.join(dest_dir, "nasm"))

    subprocess.run([os.path.join(dest_dir, "nasm"), "-v"], check=True)


if __name__ == "__main__":
    main()
