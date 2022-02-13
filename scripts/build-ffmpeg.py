import contextlib
import glob
import os
import platform
import shutil
import struct
import subprocess
import sys
import time
from typing import List

if len(sys.argv) < 2:
    sys.stderr.write("Usage: build-ffmpeg.py <prefix>\n")
    sys.exit(1)

dest_dir = sys.argv[1]
build_dir = os.path.abspath("build")
patch_dir = os.path.abspath("patches")
source_dir = os.path.abspath("source")


@contextlib.contextmanager
def log_group(title):
    start_time = time.time()
    success = False
    sys.stdout.write(f"::group::{title}\n")
    sys.stdout.flush()
    try:
        yield
        success = True
    finally:
        duration = time.time() - start_time
        outcome = "ok" if success else "failed"
        start_color = "\033[32m" if success else "\033[31m"
        end_color = "\033[0m"
        sys.stdout.write("::endgroup::\n")
        sys.stdout.write(
            f"{start_color}{outcome}{end_color} {duration:.2f}s\n".rjust(78)
        )
        sys.stdout.flush()


def build(package, configure_args=[], parallel=True):
    package_path = os.path.join(build_dir, package)

    # build package
    os.chdir(package_path)
    run(
        ["./configure"]
        + configure_args
        + ["--disable-static", "--enable-shared", "--prefix=" + dest_dir]
    )
    run(["make"] + make_args(parallel=parallel))
    run(["make", "install"])
    os.chdir(build_dir)


def build_with_cmake(package, cmake_args=[], source_dir="", parallel=True):
    package_path = os.path.join(build_dir, package)
    package_source_path = os.path.join(package_path, source_dir)
    package_build_path = os.path.join(package_path, "build")

    # determine cmake arguments
    cmake_base_args = [
        "-DBUILD_SHARED_LIBS=1",
        "-DCMAKE_INSTALL_LIBDIR=lib",
        "-DCMAKE_INSTALL_PREFIX=" + dest_dir,
    ]
    if platform.system() == "Darwin":
        cmake_base_args.append(
            "-DCMAKE_INSTALL_NAME_DIR=" + os.path.join(dest_dir, "lib")
        )

    # build package
    if not os.path.exists(package_build_path):
        os.mkdir(package_build_path)
    os.chdir(package_build_path)
    run(["cmake", package_source_path] + cmake_base_args + cmake_args)
    run(["make"] + make_args(parallel=parallel))
    run(["make", "install"])
    os.chdir(build_dir)


def get_platform():
    system = platform.system()
    machine = platform.machine()
    if system == "Linux":
        return f"manylinux_{machine}"
    elif system == "Darwin":
        # cibuildwheel sets ARCHFLAGS:
        # https://github.com/pypa/cibuildwheel/blob/5255155bc57eb6224354356df648dc42e31a0028/cibuildwheel/macos.py#L207-L220
        if "ARCHFLAGS" in os.environ:
            machine = os.environ["ARCHFLAGS"].split()[1]
        return f"macosx_{machine}"
    elif system == "Windows":
        if struct.calcsize("P") * 8 == 64:
            return "win_amd64"
        else:
            return "win32"
    else:
        raise Exception(f"Unsupported system {system}")


def make_args(*, parallel: bool) -> List[str]:
    """
    Arguments for GNU make.
    """
    args = []

    # do not parallelize build when running in qemu
    if parallel and platform.machine() != "aarch64":
        args.append("-j")

    return args


def prepend_env(name, new, separator=" "):
    old = os.environ.get(name)
    if old:
        os.environ[name] = new + separator + old
    else:
        os.environ[name] = new


def extract(package, url, *, strip_components=1):
    path = os.path.join(build_dir, package)
    patch = os.path.join(patch_dir, package + ".patch")
    tarball = os.path.join(source_dir, url.split("/")[-1])

    # download tarball
    if not os.path.exists(tarball):
        run(["curl", "-L", "-o", tarball, url])

    # extract tarball
    os.mkdir(path)
    run(["tar", "xf", tarball, "-C", path, "--strip-components", str(strip_components)])

    # apply patch
    if os.path.exists(patch):
        run(["patch", "-d", path, "-i", patch, "-p1"])


def run(cmd):
    sys.stdout.write(f"- Running: {cmd}\n")
    sys.stdout.flush()
    subprocess.run(cmd, check=True)


output_dir = os.path.abspath("output")
system = platform.system()
if system == "Linux" and os.environ.get("CIBUILDWHEEL") == "1":
    output_dir = "/output"
output_tarball = os.path.join(output_dir, f"ffmpeg-{get_platform()}.tar.gz")

for d in [build_dir, dest_dir]:
    if os.path.exists(d):
        shutil.rmtree(d)
for d in [build_dir, output_dir, source_dir]:
    if not os.path.exists(d):
        os.mkdir(d)

if not os.path.exists(output_tarball):
    os.chdir(build_dir)

    prepend_env("CPPFLAGS", "-I" + os.path.join(dest_dir, "include"))
    prepend_env("LDFLAGS", "-L" + os.path.join(dest_dir, "lib"))
    prepend_env("PATH", os.path.join(dest_dir, "bin"), separator=":")
    prepend_env(
        "PKG_CONFIG_PATH", os.path.join(dest_dir, "lib", "pkgconfig"), separator=":"
    )

    # install packages
    available_tools = set()
    if system == "Linux" and os.environ.get("CIBUILDWHEEL") == "1":
        with log_group("install packages"):
            run(["yum", "-y", "install", "gperf", "libuuid-devel", "zlib-devel"])
        available_tools.update(["gperf"])

    #### BUILD TOOLS ####

    # install cmake, meson and ninja
    with log_group("install python packages"):
        run(["pip", "install", "cmake", "meson", "ninja"])

    # build gperf if needed
    if "gperf" not in available_tools:
        with log_group("install gperf"):
            extract("gperf", "http://ftp.gnu.org/pub/gnu/gperf/gperf-3.1.tar.gz")
            build("gperf")

    # build nasm if needed
    if "nasm" not in available_tools:
        with log_group("install nasm"):
            extract(
                "nasm",
                "https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/nasm-2.14.02.tar.bz2",
            )
            build("nasm")

    #### LIBRARIES ###

    # build xz
    with log_group("xz"):
        extract("xz", "https://tukaani.org/xz/xz-5.2.5.tar.bz2")
        build("xz", ["--disable-doc", "--disable-nls"])

    # build gmp
    with log_group("gmp"):
        extract("gmp", "https://gmplib.org/download/gmp/gmp-6.2.0.tar.xz")
        build("gmp")

    # build png (requires zlib)
    with log_group("png"):
        extract(
            "png",
            "http://deb.debian.org/debian/pool/main/libp/libpng1.6/libpng1.6_1.6.37.orig.tar.gz",
        )
        build("png")

    # build xml2 (requires xz and zlib)
    with log_group("xml2"):
        extract("xml2", "ftp://xmlsoft.org/libxml2/libxml2-sources-2.9.10.tar.gz")
        build("xml2", ["--without-python"])

    # build unistring
    with log_group("unistring"):
        extract(
            "unistring",
            "https://ftp.gnu.org/gnu/libunistring/libunistring-0.9.10.tar.gz",
        )
        build("unistring")

    # build freetype (requires png)
    with log_group("freetype"):
        extract(
            "freetype",
            "https://download.savannah.gnu.org/releases/freetype/freetype-2.10.1.tar.gz",
        )
        build("freetype")

    # build fontconfig (requires freetype, libxml2 and uuid)
    with log_group("fontconfig"):
        extract(
            "fontconfig",
            "https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.13.1.tar.bz2",
        )
        build("fontconfig", ["--disable-nls", "--enable-libxml2"])

    # build fribidi
    with log_group("fribidi"):
        extract(
            "fribidi",
            "https://github.com/fribidi/fribidi/releases/download/v1.0.9/fribidi-1.0.9.tar.xz",
        )
        build("fribidi")

    # build nettle (requires gmp)
    with log_group("nettle"):
        extract("nettle", "https://ftp.gnu.org/gnu/nettle/nettle-3.6.tar.gz")
        build(
            "nettle",
            ["--disable-documentation", "--libdir=" + os.path.join(dest_dir, "lib")],
        )

    # build gnutls (requires nettle and unistring)
    with log_group("gnutls"):
        extract(
            "gnutls",
            "https://www.gnupg.org/ftp/gcrypt/gnutls/v3.6/gnutls-3.6.15.tar.xz",
        )
        build(
            "gnutls",
            [
                "--disable-cxx",
                "--disable-doc",
                "--disable-nls",
                "--disable-tests",
                "--disable-tools",
                "--with-included-libtasn1",
                "--without-p11-kit",
            ],
        )

    #### CODECS ###

    # build aom
    with log_group("aom"):
        extract(
            "aom",
            "https://aomedia.googlesource.com/aom/+archive/a6091ebb8a7da245373e56a005f2bb95be064e03.tar.gz",
            strip_components=0,
        )
        build_with_cmake(
            "aom",
            [
                "-DENABLE_DOCS=0",
                "-DENABLE_EXAMPLES=0",
                "-DENABLE_TESTS=0",
                "-DENABLE_TOOLS=0",
            ],
            parallel=False,
        )

    # build ass (requires freetype and fribidi)
    with log_group("ass"):
        extract(
            "ass",
            "https://github.com/libass/libass/releases/download/0.14.0/libass-0.14.0.tar.gz",
        )
        build("ass")

    # build bluray (requires fontconfig)
    with log_group("blueray"):
        extract(
            "bluray",
            "https://download.videolan.org/pub/videolan/libbluray/1.1.2/libbluray-1.1.2.tar.bz2",
        )
        build("bluray", ["--disable-bdjava-jar"])

    # build dav1d (requires meson, nasm and ninja)
    with log_group("dav1d"):
        extract(
            "dav1d",
            "https://code.videolan.org/videolan/dav1d/-/archive/0.9.2/dav1d-0.9.2.tar.bz2",
        )
        os.mkdir(os.path.join("dav1d", "build"))
        os.chdir(os.path.join("dav1d", "build"))
        run(["meson", "..", "--libdir=lib", "--prefix=" + dest_dir])
        run(["ninja"])
        run(["ninja", "install"])
        os.chdir(build_dir)

    # build lame
    with log_group("lame"):
        extract(
            "lame",
            "http://deb.debian.org/debian/pool/main/l/lame/lame_3.100.orig.tar.gz",
        )
        run(["sed", "-i.bak", "/^lame_init_old$/d", "lame/include/libmp3lame.sym"])
        build("lame")

    # build ogg
    with log_group("ogg"):
        extract("ogg", "http://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.gz")
        build("ogg")

    # build opencore-amr
    with log_group("opencore-amr"):
        extract(
            "opencore-amr",
            "http://deb.debian.org/debian/pool/main/o/opencore-amr/opencore-amr_0.1.5.orig.tar.gz",
        )
        build("opencore-amr")

    # build openjpeg
    with log_group("openjpeg"):
        extract(
            "openjpeg", "https://github.com/uclouvain/openjpeg/archive/v2.3.1.tar.gz"
        )
        build_with_cmake("openjpeg")

    # build opus
    with log_group("opus"):
        extract("opus", "https://archive.mozilla.org/pub/opus/opus-1.3.1.tar.gz")
        build("opus", ["--disable-extra-programs"])

    # build speex
    with log_group("speex"):
        extract("speex", "http://downloads.xiph.org/releases/speex/speex-1.2.0.tar.gz")
        build("speex", ["--disable-binaries"])

    # build twolame
    with log_group("twolame"):
        extract(
            "twolame",
            "http://deb.debian.org/debian/pool/main/t/twolame/twolame_0.4.0.orig.tar.gz",
        )
        build("twolame")

    # build vorbis (requires ogg)
    with log_group("vorbis"):
        extract(
            "vorbis", "http://downloads.xiph.org/releases/vorbis/libvorbis-1.3.6.tar.gz"
        )
        build("vorbis")

    # build theora (requires vorbis)
    with log_group("theora"):
        extract(
            "theora", "http://downloads.xiph.org/releases/theora/libtheora-1.1.1.tar.gz"
        )
        build("theora", ["--disable-examples", "--disable-spec"])

    # build wavpack
    with log_group("wavpack"):
        extract("wavpack", "http://www.wavpack.com/wavpack-5.3.0.tar.bz2")
        build("wavpack")

    # build x264
    with log_group("x264"):
        extract(
            "x264",
            "https://code.videolan.org/videolan/x264/-/archive/master/x264-master.tar.bz2",
        )
        build("x264")

    # build x265
    with log_group("x265"):
        extract("x265", "http://ftp.videolan.org/pub/videolan/x265/x265_3.2.1.tar.gz")
        build_with_cmake("x265", source_dir="source")

    # build xvid
    with log_group("xvid"):
        extract("xvid", "https://downloads.xvid.com/downloads/xvidcore-1.3.7.tar.gz")
        build("xvid/build/generic")

    # build ffmpeg
    with log_group("ffmpeg"):
        extract("ffmpeg", f"https://ffmpeg.org/releases/ffmpeg-4.3.2.tar.gz")
        build(
            "ffmpeg",
            [
                "--disable-doc",
                "--disable-libxcb",
                "--enable-fontconfig",
                "--enable-gmp",
                "--enable-gnutls",
                "--enable-gpl",
                "--enable-libaom",
                "--enable-libass",
                "--enable-libbluray",
                "--enable-libdav1d",
                "--enable-libfreetype",
                "--enable-libmp3lame",
                "--enable-libopencore-amrnb",
                "--enable-libopencore-amrwb",
                "--enable-libopenjpeg",
                "--enable-libopus",
                "--enable-libspeex",
                "--enable-libtheora",
                "--enable-libtwolame",
                "--enable-libvorbis",
                "--enable-libwavpack",
                "--enable-libx264",
                "--enable-libx265",
                "--enable-libxml2",
                "--enable-libxvid",
                "--enable-lzma",
                "--enable-version3",
                "--enable-zlib",
            ],
        )

    if system == "Darwin":
        run(["otool", "-L"] + glob.glob(os.path.join(dest_dir, "lib", "*.dylib")))

    run(["tar", "czvf", output_tarball, "-C", dest_dir, "include", "lib"])
