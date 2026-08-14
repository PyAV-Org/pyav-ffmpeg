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
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-4.0.tar.gz",
        sha256="3addbc00da01846b232fb3bc453538ea5468da43033f21bb345cb1e9073f5094",
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
        name="lamer",
        source_url="https://github.com/basswood-io/lamer/archive/refs/tags/v3.101.0.tar.gz",
        source_filename="lamer-3.101.0.tar.gz",
        sha256="81839b16fdc401e20b73389d05f32a7656008f43bcb960feff290d6f08fc109e",
        build_system="make",
    ),
    Package(
        name="opus",
        source_url="https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.6.1.tar.gz",
        sha256="6ffcb593207be92584df15b32466ed64bbec99109f007c82205f0194572411a1",
        build_arguments=["--disable-doc", "--disable-extra-programs"],
    ),
    Package(
        name="dav1d",
        source_url="https://code.videolan.org/videolan/dav1d/-/archive/1.5.4/dav1d-1.5.4.tar.bz2",
        sha256="2abfb0c89212e6e4733a54e0ae509ec00a5b845a6360946f918806e14aedb011",
        requires=["nasm"],
        build_system="meson",
        build_arguments=["-Denable_tests=false"],
    ),
    Package(
        name="libsvtav1",
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v4.2.0/SVT-AV1-v4.2.0.tar.bz2",
        sha256="512f2ea5649e3e76c2dddcc25c2556fb67a9582baaab207c9c96161c94659dad",
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
        name="libvmaf",
        source_url="https://github.com/Netflix/vmaf/archive/refs/tags/v3.2.0.tar.gz",
        source_filename="vmaf-3.2.0.tar.gz",
        sha256="a28f93f3b4fa65601be324587072e32a6a704a304ba7b1aec9b70b3f709bc1dc",
        build_system="meson",
        source_dir="libvmaf",
        requires=["nasm"],
        build_arguments=[
            "-Denable_tests=false",
            "-Denable_docs=false",
            "-Denable_tools=false",
        ],
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/b35605ace3ddf7c1a5d67a2eb553f034aef41d55/x264-b35605ace3ddf7c1a5d67a2eb553f034aef41d55.tar.bz2",
        sha256="6eeb82934e69fd51e043bd8c5b0d152839638d1ce7aa4eea65a3fedcf83ff224",
        # assembly contains textrels which are not supported by musl
        build_arguments=(
            "--disable-cli --disable-lsmash --disable-swscale --disable-ffms --disable-opencl --enable-strip" + (" --disable-asm" if is_musllinux else "")
        ).split(" "),
    ),
    Package(
        name="x265",
        source_url="https://github.com/Multicorewareinc/x265/releases/download/4.3/x265_4.3.tar.gz",
        sha256="83c53e4c8bbb8f1e33ed59e10a7d621d1d7801ca853910c3eb41f038b8ffb121",
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
    source_url="https://github.com/GPUOpen-LibrariesAndSDKs/AMF/releases/download/v1.5.2/AMF-headers-v1.5.2.tar.gz",
    sha256="d3c12eb324edf05e214608b6a395a51dd95770ed9d45520185d6c3a206811c99",
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
    source_url="https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz",
    sha256="cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635",
)

all_packages: list[Package] = [ffmpeg_package]
all_packages.extend(codec_group)
all_packages.extend(gnutls_group) 
all_packages.extend(
    [nasm_package, alsa_package, nvheaders_package, amfheaders_package, libvpl_package]
)
