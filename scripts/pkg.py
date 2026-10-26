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
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.5.tar.gz",
        sha256="5b0ecd46cbf225375f20ab4056197e66a7ac590e2684c069af407ae3383c9d81",
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
        source_url="https://github.com/webmproject/libvpx/archive/refs/tags/v1.17.0.tar.gz",
        sha256="1020f184046187baa2985dbde38e0691f49c44088bca7a1842b0236c6081dc0a",
        source_filename="vpx-1.17.0.tar.gz",
        build_arguments=[
            "--disable-examples",
            "--disable-tools",
            "--disable-unit-tests",
            "--disable-dependency-tracking",
        ],
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
            "-DWEBP_BUILD_IMG2WEBP=OFF",
            "-DWEBP_BUILD_VWEBP=OFF",
            "-DWEBP_BUILD_WEBPINFO=OFF",
            "-DWEBP_BUILD_WEBPMUX=OFF",
            "-DWEBP_BUILD_BUILD_EXTRAS=OFF",
        ],
    ),
    Package(
        name="libvmaf",
        source_url="https://github.com/Netflix/vmaf/archive/refs/tags/v3.2.1.tar.gz",
        source_filename="vmaf-3.2.1.tar.gz",
        sha256="5df7386911bc15fd1ca783132528748d219768ae4fc5f8e0b61184f041648092",
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

# libass and its dependencies. Fontconfig is not built: libass uses CoreText on
# macOS and DirectWrite on Windows, and on Linux only fonts given by path or
# attached to the file.
ass_group = [
    Package(
        name="freetype",
        source_url="https://download.savannah.gnu.org/releases/freetype/freetype-2.15.0.tar.xz",
        sha256="93cd47eb719c325107f2d3cf087d06299e944c3b48a40b55537302304dea1dd5",
        build_system="cmake",
        build_arguments=[
            "-DFT_DISABLE_ZLIB=ON",
            "-DFT_DISABLE_BZIP2=ON",
            "-DFT_DISABLE_PNG=ON",
            "-DFT_DISABLE_HARFBUZZ=ON",
            "-DFT_DISABLE_BROTLI=ON",
            "-DFT_DISABLE_HVF=ON",
        ],
    ),
    Package(
        name="fribidi",
        source_url="https://github.com/fribidi/fribidi/releases/download/v1.0.17/fribidi-1.0.17.tar.xz",
        sha256="6949dcde27d41cebad1fd741fcafc36d55a1020d2d872d4a6eb3914caabbada2",
        build_system="meson",
        build_arguments=["-Ddocs=false", "-Dbin=false", "-Dtests=false"],
    ),
    Package(
        name="harfbuzz",
        source_url="https://github.com/harfbuzz/harfbuzz/releases/download/15.0.0/harfbuzz-15.0.0.tar.xz",
        sha256="968536e9abd782f07f7954044c0c4020199fcdd39b41d221ec42d2a3be4a44df",
        build_system="meson",
        build_arguments=[
            "--auto-features=disabled",
            "-Dtests=disabled",
            "-Ddocs=disabled",
            "-Dutilities=disabled",
            "-Dintrospection=disabled",
            "-Dbenchmark=disabled",
            "-Draster=disabled",
            "-Dvector=disabled",
            "-Dgpu=disabled",
            "-Dsubset=disabled",
        ],
    ),
    Package(
        name="libass",
        source_url="https://github.com/libass/libass/releases/download/0.17.5/libass-0.17.5.tar.xz",
        sha256="2dca25c0e0c837ddf00b52011b3f82cac1e4ddd3ad018227806b0c2288864acc",
        build_system="meson",
        requires=["freetype", "fribidi", "harfbuzz"],
        build_arguments=[
            "--auto-features=disabled",
            "-Dtest=disabled",
            "-Dcompare=disabled",
            "-Dprofile=disabled",
            "-Dfuzz=disabled",
            "-Dcheckasm=disabled",
            "-Dlibunibreak=disabled",
            "-Dfontconfig=disabled",
        ],
    ),
]

alsa_package = Package(
    name="alsa-lib",
    source_url="https://www.alsa-project.org/files/pub/lib/alsa-lib-1.2.16.1.tar.bz2",
    sha256="f740db7f488255944ffd4428416ee3390a96742856916433df468c281436480e",
    build_arguments=["--disable-python"],
)

nvheaders_package = Package(
    name="nv-codec-headers",
    source_url="https://github.com/FFmpeg/nv-codec-headers/archive/refs/tags/n13.0.19.1.tar.gz",
    sha256="c293161bd92dac53f2f8fab08abcd4f96773c3644a57b23c2260b4be2311ab2f",
    build_system="make",
)

amfheaders_package = Package(
    name="amf-headers",
    source_url="https://github.com/GPUOpen-LibrariesAndSDKs/AMF/releases/download/v1.5.3/AMF-headers-v1.5.3.tar.gz",
    sha256="0f521ad98041f8001147cded4a660127f18b1c27a801a5cd691bda1fa48381be",
    build_system="make",
)

libvpl_package = Package(
    name="libvpl",
    source_url="https://github.com/intel/libvpl/archive/refs/tags/v2.17.0.tar.gz",
    sha256="4de3e2faf1e8307fb282e4a43f443191810f6a6b0a484fffa7995ba1c814c6ec",
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
    source_url="https://www.nasm.us/pub/nasm/releasebuilds/3.02/nasm-3.02.tar.xz",
    sha256="87336eba53b4acfe917424ab5d500d2b0054d9f5148d35c2273ccf2cfb712f0d",
)

ffmpeg_package = Package(
    name="ffmpeg",
    source_url="https://ffmpeg.org/releases/ffmpeg-9.0.2.tar.xz",
    sha256="8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e",
)

all_packages: list[Package] = [ffmpeg_package]
all_packages.extend(codec_group)
all_packages.extend(ass_group)
all_packages.extend(gnutls_group) 
all_packages.extend(
    [nasm_package, alsa_package, nvheaders_package, amfheaders_package, libvpl_package]
)
