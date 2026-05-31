import argparse
import glob
import gzip
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile

from cibuildpkg import Builder, Package, fetch, log_group, run
from pkg import *

plat = platform.system()


def make_archive_deterministic(path: str) -> None:
    """Zero mtime/uid/gid in every ar member header to make the archive reproducible.

    Static archives (.a files) embed the file modification time (and uid/gid) of
    each member in a 60-byte header.  Tools like ar(1), libtool -static, and ar -M
    do not always produce deterministic timestamps even when SOURCE_DATE_EPOCH is set
    or the -D flag is requested, especially in custom CMake commands (e.g. x265's
    multi-lib merge).  Zeroing these fields in-place is the safest cross-platform fix.
    """
    MAGIC = b"!<arch>\n"
    HEADER_SIZE = 60
    with open(path, "r+b") as f:
        if f.read(len(MAGIC)) != MAGIC:
            return
        while True:
            pos = f.tell()
            header = f.read(HEADER_SIZE)
            if len(header) < HEADER_SIZE:
                break
            if header[58:60] != b"`\n":
                break  # not a valid ar member header
            try:
                size = int(header[48:58].decode().strip())
            except ValueError:
                break
            # ar member header layout (60 bytes):
            #   [0:16]  name          16 bytes
            #   [16:28] mtime         12 bytes  ← zero this
            #   [28:34] uid            6 bytes  ← zero this
            #   [34:40] gid            6 bytes  ← zero this
            #   [40:48] mode           8 bytes
            #   [48:58] size          10 bytes
            #   [58:60] end magic      2 bytes  (`\n)
            patched = (
                header[:16]
                + b"0           "  # mtime: 12 bytes
                + b"0     "        # uid:    6 bytes
                + b"0     "        # gid:    6 bytes
                + header[40:]      # mode + size + end magic unchanged
            )
            f.seek(pos)
            f.write(patched)
            # advance past member data; ar pads to even offset
            f.seek(size + (size % 2), 1)


def make_tarball_name() -> str:
    machine = platform.machine().lower()
    isArm64 = machine in {"arm64", "aarch64"}

    if sys.platform.startswith("win"):
        return "ffmpeg-windows-aarch64" if isArm64 else "ffmpeg-windows-x86_64"

    elif sys.platform.startswith("darwin"):
        return "ffmpeg-macos-arm64" if isArm64 else "ffmpeg-macos-x86_64"

    elif sys.platform.startswith("linux"):
        prefix = "ffmpeg-musllinux-" if is_musllinux else "ffmpeg-manylinux-"
        # Inside the manylinux/musllinux container AUDITWHEEL_ARCH is the
        # canonical wheel arch. uname (platform.machine) is unreliable when
        # cross-building 32-bit ARM under an aarch64 kernel, where it reports
        # "armv8l" rather than "armv7l".
        return prefix + os.environ.get("AUDITWHEEL_ARCH", machine)

    else:
        return "ffmpeg-unknown"

def main():
    parser = argparse.ArgumentParser("build-ffmpeg")
    parser.add_argument("destination")

    args = parser.parse_args()
    dest_dir = os.path.abspath(args.destination)

    machine = platform.machine().lower()
    is_arm32 = machine in {"armv7l", "armv8l", "arm"}
    is_arm = machine in {"arm64", "aarch64"} or is_arm32
    is_riscv = machine in {"riscv64"}

    use_alsa = plat == "Linux"
    # CUDA, AMF, and Intel VPL are not available on ARM64 Windows
    use_cuda = plat in {"Linux", "Windows"} and not is_arm and not is_riscv
    use_amf = plat in {"Linux", "Windows"} and not is_arm and not is_riscv

    # Use Intel VPL (Video Processing Library) if supported to enable Intel QSV (Quick Sync Video)
    # hardware encoders/decoders on modern integrated and discrete Intel GPUs.
    use_libvpl = plat in {"Linux", "Windows"} and not is_arm

    # Use GnuTLS only on Linux, FFmpeg has native TLS backends for macOS and Windows.
    use_gnutls = plat == "Linux"

    output_dir = os.path.abspath("output")
    if plat == "Linux" and os.environ.get("CIBUILDWHEEL") == "1":
        output_dir = "/output"

    output_tarball = os.path.join(output_dir, make_tarball_name() + ".tar.gz")
    if os.path.exists(output_tarball):
        return

    builder = Builder(dest_dir=dest_dir)
    builder.create_directories()

    # install packages
    available_tools = set()
    if plat == "Windows":
        if not is_arm:
            available_tools.update(["nasm"])

        # print tool locations
        print("PATH", os.environ["PATH"])
        if is_arm:
            tools = ["clang", "clang++", "curl", "ld", "pkg-config"]
        else:
            tools = ["gcc", "g++", "curl", "ld", "nasm", "pkg-config"]
        for tool in tools:
            run(["where", tool])

    with log_group("install python packages"):
        run(["pip", "install", "cmake", "meson", "ninja"])

    ffmpeg_package.build_arguments = [
        "--disable-programs",
        "--disable-doc",
        "--disable-libxml2",
        "--disable-lzma",  # or re-add xz package
        "--disable-libtheora",
        "--disable-libfreetype",
        "--disable-libfontconfig",
        "--disable-libbluray",
        "--disable-libopenjpeg",
        (
            "--enable-mediafoundation"
            if plat == "Windows"
            else "--disable-mediafoundation"
        ),
        "--enable-version3",
        "--enable-alsa" if use_alsa else "--disable-alsa",
        "--enable-gnutls" if use_gnutls else "--disable-gnutls",
        "--enable-libdav1d",
        "--enable-libmp3lame",
        "--enable-libopencore-amrnb",
        "--enable-libopencore-amrwb",
        "--enable-libopus",
        "--enable-libsvtav1",
        "--enable-libvpx",
        "--enable-libwebp",
        "--enable-libxcb" if plat == "Linux" else "--disable-libxcb",
        "--enable-zlib",
    ]

    # x264/x265 are skipped on 32-bit ARM (armv7)
    if not is_arm32:
        ffmpeg_package.build_arguments.extend(
            ["--enable-libx264", "--enable-libx265"]
        )

    if use_cuda:
        ffmpeg_package.build_arguments.extend(["--enable-nvenc", "--enable-nvdec"])

    if use_amf:
        ffmpeg_package.build_arguments.append("--enable-amf")

    if use_libvpl:
        ffmpeg_package.build_arguments.append("--enable-libvpl")

    if plat == "Darwin":
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-videotoolbox",
                "--enable-audiotoolbox",
                "--extra-ldflags=-Wl,-ld_classic",
            ]
        )

    if plat == "Linux" and "RUNNER_ARCH" in os.environ:
        # FFmpeg expects "arm" for 32-bit ARM, not the uname "armv7l".
        ff_arch = "arm" if is_arm32 else machine
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-cross-compile",
                "--target-os=linux",
                "--arch=" + ff_arch,
                "--cc=/opt/clang/bin/clang",
                "--cxx=/opt/clang/bin/clang++",
            ]
        )

    if plat == "Windows" and is_arm:
        ffmpeg_package.build_arguments.extend(
            ["--cc=clang", "--cxx=clang++", "--arch=aarch64"]
        )

    ffmpeg_package.build_arguments.extend(
        [
            "--disable-encoder=avui,dca,mlp,opus,s302m,sonic,sonic_ls,truehd",
            "--disable-decoder=sonic",
            "--disable-libjack",
            "--disable-indev=jack",
            "--disable-filter=gfxcapture",  # gfxcapture_winrt C++ causes build failure on Win Arm
        ]
    )

    packages = []
    if plat != "Darwin" and "nasm" not in available_tools and machine in {"x86_64", "amd64", "i686", "i386"}:
        packages.append(nasm_package)
    if use_alsa:
        packages += [alsa_package]
    if use_cuda:
        packages += [nvheaders_package]
    if use_amf:
        packages += [amfheaders_package]
    if use_libvpl:
        packages += [libvpl_package]

    if use_gnutls:
        packages += gnutls_group
    if is_arm32:
        # x264/x265 are not built on 32-bit ARM (armv7)
        packages += [p for p in codec_group if p.name not in {"x264", "x265"}]
    else:
        packages += codec_group
    packages += [ffmpeg_package]

    # Disable runtime CPU detection for opus on Windows ARM64
    # (no CPU detection method available for this platform)
    if plat == "Windows" and is_arm:
        for pkg in packages:
            if pkg.name == "opus":
                pkg.build_arguments.append("--disable-rtcd")
                break

    for package in packages:
        builder.build(package, for_builder=package.name == "nasm")

    if plat == "Windows":
        # fix .lib files being installed in the wrong directory
        for name in (
            "avcodec",
            "avdevice",
            "avfilter",
            "avformat",
            "avutil",
            "postproc",
            "swresample",
            "swscale",
        ):
            if os.path.exists(os.path.join(dest_dir, "bin", name + ".lib")):
                shutil.move(
                    os.path.join(dest_dir, "bin", name + ".lib"),
                    os.path.join(dest_dir, "lib"),
                )

        # copy some libraries provided by mingw
        is_arm64 = machine in {"arm64", "aarch64"}
        compiler = "clang" if is_arm64 else "gcc"
        mingw_bindir = os.path.dirname(
            subprocess.run(["where", compiler], check=True, stdout=subprocess.PIPE)
            .stdout.decode()
            .splitlines()[0]
            .strip()
        )
        if is_arm64:
            # CLANGARM64 uses clang/libc++ instead of gcc/libstdc++
            dll_names = (
                "libc++.dll",
                "libiconv-2.dll",
                "libunwind.dll",
                "libwinpthread-1.dll",
                "zlib1.dll",
            )
        else:
            dll_names = (
                "libgcc_s_seh-1.dll",
                "libiconv-2.dll",
                "libstdc++-6.dll",
                "libwinpthread-1.dll",
                "zlib1.dll",
            )
        for name in dll_names:
            shutil.copy(os.path.join(mingw_bindir, name), os.path.join(dest_dir, "bin"))

    # find libraries
    if plat == "Darwin":
        libraries = glob.glob(os.path.join(dest_dir, "lib", "*.dylib"))
    elif plat == "Linux":
        libraries = glob.glob(os.path.join(dest_dir, "lib", "*.so"))
    elif plat == "Windows":
        libraries = glob.glob(os.path.join(dest_dir, "bin", "*.dll"))

    if plat == "Darwin":
        run(["strip", "-x", "-S"] + libraries)
    else:
        run(["strip", "-s"] + libraries)

    for lib in glob.glob(os.path.join(dest_dir, "lib", "*.a")):
        make_archive_deterministic(lib)

    # build output tarball (reproducible: fixed timestamps, sorted entries)
    os.makedirs(output_dir, exist_ok=True)
    subdirs = ["include", "lib"]
    if plat == "Windows":
        subdirs.append("bin")
    with gzip.GzipFile(output_tarball, "wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w|") as tar:
            for subdir in subdirs:
                subdir_path = os.path.join(dest_dir, subdir)
                if not os.path.exists(subdir_path):
                    continue
                for root, dirs, files in os.walk(subdir_path):
                    dirs.sort()
                    for name in sorted(files):
                        if subdir == "bin" and not name.endswith(".dll"):
                            continue
                        filepath = os.path.join(root, name)
                        arcname = os.path.relpath(filepath, dest_dir)
                        info = tar.gettarinfo(filepath, arcname=arcname)
                        info.mtime = 0
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        if info.issym() or info.islnk():
                            tar.addfile(info)
                        else:
                            with open(filepath, "rb") as f:
                                tar.addfile(info, f)


if __name__ == "__main__":
    main()
