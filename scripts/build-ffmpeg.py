import argparse
import concurrent.futures
import glob
import hashlib
import os
import platform
import shutil
import subprocess
import sys

from cibuildpkg import Builder, Package, When, fetch, log_group, run

plat = platform.system()
is_musllinux = plat == "Linux" and platform.libc_ver()[0] != "glibc"


def calculate_sha256(filename: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

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
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.4.1.tar.gz",
        sha256="12542ad7619470efd95a623174dcd4b364f2483caf708c6bee837cb53a54cb9d",
    ),
    Package(
        name="nettle",
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-3.10.2.tar.gz",
        sha256="fe9ff51cb1f2abb5e65a6b8c10a92da0ab5ab6eaf26e7fc2b675c45f1fb519b5",
        requires=["gmp"],
        build_arguments=["--disable-documentation"],
        # build randomly fails with "*** missing separator.  Stop."
        build_parallel=False,
    ),
    Package(
        name="gnutls",
        source_url="https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.11.tar.xz",
        sha256="91bd23c4a86ebc6152e81303d20cf6ceaeb97bc8f84266d0faec6e29f17baa20",
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
        name="ogg",
        source_url="http://downloads.xiph.org/releases/ogg/libogg-1.3.6.tar.gz",
        sha256="83e6704730683d004d20e21b8f7f55dcb3383cdf84c0daedf30bde175f774638",
    ),
    Package(
        name="opus",
        source_url="https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.6.tar.gz",
        sha256="b7637334527201fdfd6dd6a02e67aceffb0e5e60155bbd89175647a80301c92c",
        build_arguments=["--disable-doc", "--disable-extra-programs"],
    ),
    Package(
        name="speex",
        source_url="http://downloads.xiph.org/releases/speex/speex-1.2.1.tar.gz",
        sha256="4b44d4f2b38a370a2d98a78329fefc56a0cf93d1c1be70029217baae6628feea",
        build_arguments=["--disable-binaries"],
    ),
    Package(
        name="vorbis",
        source_url="https://ftp.osuosl.org/pub/xiph/releases/vorbis/libvorbis-1.3.7.tar.xz",
        sha256="b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b",
        requires=["ogg"],
    ),
    Package(
        name="aom",
        source_url="https://storage.googleapis.com/aom-releases/libaom-3.13.1.tar.gz",
        sha256="19e45a5a7192d690565229983dad900e76b513a02306c12053fb9a262cbeca7d",
        build_system="cmake",
        build_arguments=[
            "-DENABLE_DOCS=0",
            "-DENABLE_EXAMPLES=0",
            "-DENABLE_TESTS=0",
            "-DENABLE_TOOLS=0",
        ],
        build_parallel=False,
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
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v3.1.2/SVT-AV1-v3.1.2.tar.bz2",
        sha256="802e9bb2b14f66e8c638f54857ccb84d3536144b0ae18b9f568bbf2314d2de88",
        build_system="cmake",
        build_arguments=["-DBUILD_APPS=OFF", "-DENABLE_NASM=ON"],
    ),
    Package(
        name="vpx",
        source_url="https://github.com/webmproject/libvpx/archive/refs/tags/v1.15.2.tar.gz",
        sha256="26fcd3db88045dee380e581862a6ef106f49b74b6396ee95c2993a260b4636aa",
        source_filename="vpx-1.15.2.tar.gz",
        build_arguments=[
            "--disable-examples",
            "--disable-tools",
            "--disable-unit-tests",
            "--disable-dependency-tracking",
        ],
    ),
    Package(
        name="png",
        source_url="https://downloads.sourceforge.net/project/libpng/libpng16/1.6.53/libpng-1.6.53.tar.xz",
        sha256="1d3fb8ccc2932d04aa3663e22ef5ef490244370f4e568d7850165068778d98d4",
        # avoid an assembler error on Windows
        build_arguments=["PNG_COPTS=-fno-asynchronous-unwind-tables"],
    ),
    Package(
        name="webp",
        source_url="https://github.com/webmproject/libwebp/archive/refs/tags/v1.5.0.tar.gz",
        sha256="668c9aba45565e24c27e17f7aaf7060a399f7f31dba6c97a044e1feacb930f37",
        source_filename="webp-1.5.0.tar.gz",
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
        name="openh264",
        source_url="https://github.com/cisco/openh264/archive/refs/tags/v2.6.0.tar.gz",
        sha256="558544ad358283a7ab2930d69a9ceddf913f4a51ee9bf1bfb9e377322af81a69",
        source_filename="openh264-2.6.0.tar.gz",
        build_system="meson",
    ),
    Package(
        name="opencore-amr",
        source_url="https://downloads.sourceforge.net/project/opencore-amr/opencore-amr/opencore-amr-0.1.6.tar.gz",
        sha256="483eb4061088e2b34b358e47540b5d495a96cd468e361050fae615b1809dc4a1",
        # parallel build hangs on Windows
        build_parallel=plat != "Windows",
        when=When.community_only,
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/32c3b801191522961102d4bea292cdb61068d0dd/x264-32c3b801191522961102d4bea292cdb61068d0dd.tar.bz2",
        sha256="d7748f350127cea138ad97479c385c9a35a6f8527bc6ef7a52236777cf30b839",
        # assembly contains textrels which are not supported by musl
        build_arguments=["--disable-cli"] + (["--disable-asm"] if is_musllinux else []),
        # parallel build runs out of memory on Windows
        build_parallel=plat != "Windows",
    ),
    Package(
        name="x265",
        source_url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_4.1.tar.gz",
        sha256="a31699c6a89806b74b0151e5e6a7df65de4b49050482fe5ebf8a4379d7af8f29",
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

ffmpeg_package = Package(
    name="ffmpeg",
    source_url="https://ffmpeg.org/releases/ffmpeg-8.0.1.tar.xz",
    sha256="05ee0b03119b45c0bdb4df654b96802e909e0a752f72e4fe3794f487229e5a41",
    build_arguments=[],
    build_parallel=plat != "Windows",
)


def download_and_verify_package(package: Package) -> None:
    tarball = os.path.join(
        os.path.abspath("source"),
        package.source_filename or package.source_url.split("/")[-1],
    )

    if not os.path.exists(tarball):
        try:
            fetch(package.source_url, tarball)
        except subprocess.CalledProcessError:
            pass

    if not os.path.exists(tarball):
        raise ValueError(f"tar bar doesn't exist: {tarball}")

    sha = calculate_sha256(tarball)
    if package.sha256 == sha:
        print(f"{package.name} tarball: hashes match")
    else:
        raise ValueError(
            f"sha256 hash of {package.name} tarball do not match!\nExpected: {package.sha256}\nGot: {sha}"
        )


def download_tars(packages: list[Package]) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_package = {
            executor.submit(download_and_verify_package, package): package.name
            for package in packages
        }

        for future in concurrent.futures.as_completed(future_to_package):
            name = future_to_package[future]
            try:
                future.result()
            except Exception as exc:
                print(f"{name} generated an exception: {exc}")
                raise

def make_tarball_name() -> str:
    machine = platform.machine().lower()
    isArm64 = machine in {"arm64", "aarch64"}

    if sys.platform.startswith("win"):
        return "ffmpeg-windows-aarch64" if isArm64 else "ffmpeg-windows-x86_64"

    elif sys.platform.startswith("darwin"):
        return "ffmpeg-macos-arm64" if isArm64 else "ffmpeg-macos-x86_64"

    elif sys.platform.startswith("linux"):
        prefix = "ffmpeg-musllinux-" if is_musllinux else "ffmpeg-manylinux-"
        return prefix + machine

    else:
        return "ffmpeg-unknown"

def main():
    parser = argparse.ArgumentParser("build-ffmpeg")
    parser.add_argument("destination")
    parser.add_argument("--community", action="store_true")

    args = parser.parse_args()

    dest_dir = os.path.abspath(args.destination)
    community = args.community

    # Use ALSA only on Linux.
    use_alsa = plat == "Linux"

    # Use CUDA if supported.
    use_cuda = plat in {"Linux", "Windows"}

    # Use AMD AMF if supported.
    use_amf = plat in {"Linux", "Windows"}

    # Use Intel VPL (Video Processing Library) if supported to enable Intel QSV (Quick Sync Video)
    # hardware encoders/decoders on modern integrated and discrete Intel GPUs.
    use_libvpl = plat in {"Linux", "Windows"}

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
        available_tools.update(["nasm"])

        # print tool locations
        print("PATH", os.environ["PATH"])
        for tool in ["gcc", "g++", "curl", "ld", "nasm", "pkg-config"]:
            run(["where", tool])

    with log_group("install python packages"):
        run(["pip", "install", "cmake==3.31.10", "meson", "ninja"])

    # build tools
    build_tools = []
    if "nasm" not in available_tools and platform.machine() not in {"arm64", "aarch64"}:
        build_tools.append(
            Package(
                name="nasm",
                source_url="https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/nasm-2.16.03.tar.xz",
                sha256="1412a1c760bbd05db026b6c0d1657affd6631cd0a63cddb6f73cc6d4aa616148",
            )
        )

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
        "--enable-libaom",
        "--enable-libdav1d",
        "--enable-libmp3lame",
        "--enable-libopencore-amrnb" if community else "--disable-libopencore-amrnb",
        "--enable-libopencore-amrwb" if community else "--disable-libopencore-amrwb",
        "--enable-libopus",
        "--enable-libspeex",
        "--enable-libsvtav1",
        "--enable-libvorbis",
        "--enable-libvpx",
        "--enable-libwebp",
        "--enable-libopenh264",
        "--enable-libxcb" if plat == "Linux" else "--disable-libxcb",
        "--enable-zlib",
        "--enable-libx264",
        "--enable-libx265",
    ]

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
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-cross-compile",
                "--target-os=linux",
                "--arch=" + platform.machine().lower(),
                "--cc=/opt/clang/bin/clang",
                "--cxx=/opt/clang/bin/clang++",
            ]
        )

    ffmpeg_package.build_arguments.extend(
        [
            "--disable-encoder=avui,dca,mlp,opus,s302m,sonic,sonic_ls,truehd,vorbis",
            "--disable-decoder=sonic",
            "--disable-libjack",
            "--disable-indev=jack",
        ]
    )

    packages = []
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
    packages += codec_group
    packages += [ffmpeg_package]

    filtered_packages = []
    for package in packages:
        if package.when == When.community_only and not community:
            continue
        if package.when == When.commercial_only and community:
            continue
        filtered_packages.append(package)

    download_tars(build_tools + filtered_packages)
    for tool in build_tools:
        builder.build(tool, for_builder=True)
    for package in filtered_packages:
        builder.build(package)

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
        mingw_bindir = os.path.dirname(
            subprocess.run(["where", "gcc"], check=True, stdout=subprocess.PIPE)
            .stdout.decode()
            .splitlines()[0]
            .strip()
        )
        for name in (
            "libgcc_s_seh-1.dll",
            "libiconv-2.dll",
            "libstdc++-6.dll",
            "libwinpthread-1.dll",
            "zlib1.dll",
        ):
            shutil.copy(os.path.join(mingw_bindir, name), os.path.join(dest_dir, "bin"))

    # find libraries
    if plat == "Darwin":
        libraries = glob.glob(os.path.join(dest_dir, "lib", "*.dylib"))
    elif plat == "Linux":
        libraries = glob.glob(os.path.join(dest_dir, "lib", "*.so"))
    elif plat == "Windows":
        libraries = glob.glob(os.path.join(dest_dir, "bin", "*.dll"))

    # strip libraries
    if plat == "Darwin":
        run(["strip", "-S"] + libraries)
        run(["otool", "-L"] + libraries)
    else:
        run(["strip", "-s"] + libraries)

    # build output tarball
    os.makedirs(output_dir, exist_ok=True)
    run(["tar", "czvf", output_tarball, "-C", dest_dir, "bin", "include", "lib"])


if __name__ == "__main__":
    main()
