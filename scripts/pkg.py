from dataclasses import dataclass, field
import platform

@dataclass(slots=True)
class Package:
    name: str
    source_url: str
    sha256: str
    build_system: str = "autoconf"
    build_arguments: list[str] = field(default_factory=list)
    build_dir: str = "build"
    build_parallel: bool = True
    requires: list[str] = field(default_factory=list)
    source_dir: str = ""
    source_filename: str = ""

    def __lt__(self, other):
        return self.name < other.name

plat = platform.system()
is_musllinux = plat == "Linux" and platform.libc_ver()[0] != "glibc"

gnutls_group = [
    Package(
        name="gmp",
        source_url="https://ftp.gnu.org/gnu/gmp/gmp-6.3.0.tar.xz",
        sha256="a3c2b80201b89e68616f4ad30bc66aee4927c3ce50e33929ca819d5c43538898",
        # out-of-tree builds fail on Windows
        build_dir=".",
    ),
    Package(
        name="unistring",
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.4.2.tar.gz",
        sha256="e82664b170064e62331962126b259d452d53b227bb4a93ab20040d846fec01d8",
    ),
    Package(
        name="nettle",
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-3.10.2.tar.gz",
        sha256="fe9ff51cb1f2abb5e65a6b8c10a92da0ab5ab6eaf26e7fc2b675c45f1fb519b5",
        requires=["gmp"],
        build_arguments=["--disable-documentation"],
    ),
    Package(
        name="gnutls",
        source_url="https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.13.tar.xz",
        sha256="ffed8ec1bf09c2426d4f14aae377de4753b53e537d685e604e99a8b16ca9c97e",
        requires=["nettle", "unistring"],
        build_arguments=[
            "--disable-cxx",
            "--disable-doc",
            "--disable-guile",
            "--disable-libdane",
            "--disable-nls",
            "--disable-tests",
            "--disable-tools",
            "--with-included-libtasn1",
            "--without-p11-kit",
        ],
    ),
]

codec_group = [
    Package(
        name="lame",
        source_url="http://deb.debian.org/debian/pool/main/l/lame/lame_3.100.orig.tar.gz",
        sha256="ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e",
        build_arguments=["--disable-gtktest"],
    ),
    Package(
        name="opus",
        source_url="https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.6.1.tar.gz",
        sha256="6ffcb593207be92584df15b32466ed64bbec99109f007c82205f0194572411a1",
        build_arguments=["--disable-doc", "--disable-extra-programs"],
    ),
    Package(
        name="dav1d",
        source_url="https://code.videolan.org/videolan/dav1d/-/archive/1.5.3/dav1d-1.5.3.tar.bz2",
        sha256="e099f53253f6c247580c554d53a13f1040638f2066edc3c740e4c2f15174ce22",
        requires=["nasm"],
        build_system="meson",
    ),
    Package(
        name="libsvtav1",
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v4.1.0/SVT-AV1-v4.1.0.tar.bz2",
        sha256="184162d3db3a4448882b17230413b4938ca252eef6b3c5e2f1236b2fcf497881",
        build_system="cmake",
        build_arguments=["-DBUILD_APPS=OFF", "-DBUILD_DEC=OFF", "-DBUILD_ENC=ON", "-DENABLE_NASM=ON"],
    ),
    Package(
        name="vpx",
        source_url="https://github.com/webmproject/libvpx/archive/refs/tags/v1.16.0.tar.gz",
        sha256="7a479a3c66b9f5d5542a4c6a1b7d3768a983b1e5c14c60a9396edc9b649e015c",
        source_filename="vpx-1.16.0.tar.gz",
        build_arguments=[
            "--disable-examples",
            "--disable-tools",
            "--disable-unit-tests",
            "--disable-dependency-tracking",
        ],
    ),
    Package(
        name="png",
        source_url="https://downloads.sourceforge.net/project/libpng/libpng16/1.6.58/libpng-1.6.58.tar.xz",
        sha256="28eb403f51f0f7405249132cecfe82ea5c0ef97f1b32c5a65828814ae0d34775",
        # avoid an assembler error on Windows
        build_arguments=["PNG_COPTS=-fno-asynchronous-unwind-tables"],
    ),
    Package(
        name="webp",
        source_url="https://github.com/webmproject/libwebp/archive/refs/tags/v1.6.0.tar.gz",
        sha256="93a852c2b3efafee3723efd4636de855b46f9fe1efddd607e1f42f60fc8f2136",
        source_filename="webp-1.6.0.tar.gz",
        build_system="cmake",
        build_arguments=[
            "-DWEBP_BUILD_ANIM_UTILS=OFF",
            "-DWEBP_BUILD_CWEBP=OFF",
            "-DWEBP_BUILD_DWEBP=OFF",
            "-DWEBP_BUILD_GIF2WEBP=OFF",
            "-DWE[118;1:3uBP_BUILD_IMG2WEBP=OFF",
            "-DWEBP_BUILD_VWEBP=OFF",
            "-DWEBP_BUILD_WEBPINFO=OFF",
            "-DWEBP_BUILD_WEBPMUX=OFF",
            "-DWEBP_BUILD_BUILD_EXTRAS=OFF",
        ],
    ),
    Package(
        name="opencore-amr",
        source_url="https://downloads.sourceforge.net/project/opencore-amr/opencore-amr/opencore-amr-0.1.6.tar.gz",
        sha256="483eb4061088e2b34b358e47540b5d495a96cd468e361050fae615b1809dc4a1",
        build_arguments=["--disable-dependency-tracking"],
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/b35605ace3ddf7c1a5d67a2eb553f034aef41d55/x264-b35605ace3ddf7c1a5d67a2eb553f034aef41d55.tar.bz2",
        sha256="6eeb82934e69fd51e043bd8c5b0d152839638d1ce7aa4eea65a3fedcf83ff224",
        # assembly contains textrels which are not supported by musl
        build_arguments=(
            "--disable-cli --disable-lsmash --disable-swscale --disable-ffms --enable-strip" + (" --disable-asm" if is_musllinux else "")
        ).split(" "),
    ),
    Package(
        name="x265",
        source_url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_4.2.tar.gz",
        sha256="40b1ea0453e0309f0eba934e0ddf533f8f6295966679e8894e8f1c1c8d5e1210",
        build_system="cmake",
        source_dir="source",
    ),
]

alsa_package = Package(
    name="alsa-lib",
    source_url="https://www.alsa-project.org/files/pub/lib/alsa-lib-1.2.14.tar.bz2",
    sha256="be9c88a0b3604367dd74167a2b754a35e142f670292ae47a2fdef27a2ee97a32",
    build_arguments=["--disable-python"],
)

nvheaders_package = Package(
    name="nv-codec-headers",
    source_url="https://github.com/FFmpeg/nv-codec-headers/archive/refs/tags/n13.0.19.0.tar.gz",
    sha256="86d15d1a7c0ac73a0eafdfc57bebfeba7da8264595bf531cf4d8db1c22940116",
    build_system="make",
)

amfheaders_package = Package(
    name="amf-headers",
    source_url="https://github.com/GPUOpen-LibrariesAndSDKs/AMF/releases/download/v1.5.0/AMF-headers-v1.5.0.tar.gz",
    sha256="d569647fa26f289affe81a206259fa92f819d06db1e80cc334559953e82a3f01",
    build_system="make",
)

libvpl_package = Package(
    name="libvpl",
    source_url="https://github.com/intel/libvpl/archive/refs/tags/v2.16.0.tar.gz",
    sha256="d60931937426130ddad9f1975c010543f0da99e67edb1c6070656b7947f633b6",
    build_system="cmake",
    build_arguments=[
        "-DINSTALL_LIB=ON",
        "-DINSTALL_DEV=ON",
        "-DINSTALL_EXAMPLES=OFF",
        "-DBUILD_EXPERIMENTAL=OFF",
        "-DBUILD_TESTS=OFF",
        "-DBUILD_EXAMPLES=OFF",
    ],
)

nasm_package = Package(
    name="nasm",
    source_url="https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/nasm-2.16.03.tar.xz",
    sha256="1412a1c760bbd05db026b6c0d1657affd6631cd0a63cddb6f73cc6d4aa616148",
)

ffmpeg_package = Package(
    name="ffmpeg",
    source_url="https://ffmpeg.org/releases/ffmpeg-8.1.tar.xz",
    sha256="b072aed6871998cce9b36e7774033105ca29e33632be5b6347f3206898e0756a",
)

all_packages: list[Package] = [ffmpeg_package]
all_packages.extend(codec_group)
all_packages.extend(gnutls_group) 
all_packages.extend(
    [nasm_package, alsa_package, nvheaders_package, amfheaders_package, libvpl_package]
)
