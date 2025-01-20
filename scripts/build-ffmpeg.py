import argparse
import glob
import os
import platform
import shutil
import subprocess

from cibuildpkg import Builder, Package, fetch, get_platform, log_group, run


plat = platform.system()

library_group = [
    Package(
        name="xz",
        source_url="https://github.com/tukaani-project/xz/releases/download/v5.6.3/xz-5.6.3.tar.xz",
        build_arguments=[
            "--disable-doc",
            "--disable-lzma-links",
            "--disable-lzmadec",
            "--disable-lzmainfo",
            "--disable-nls",
            "--disable-scripts",
            "--disable-xz",
            "--disable-xzdec",
        ],
    ),
    Package(
        name="gmp",
        source_url="https://ftp.gnu.org/gnu/gmp/gmp-6.3.0.tar.xz",
        # out-of-tree builds fail on Windows
        build_dir=".",
    ),
    Package(
        name="xml2",
        requires=["xz"],
        source_url="https://download.gnome.org/sources/libxml2/2.9/libxml2-2.9.13.tar.xz",
        build_arguments=["--without-python"],
    ),
]

gnutls_group = [
    Package(
        name="unistring",
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.2.tar.gz",
    ),
    Package(
        name="nettle",
        requires=["gmp"],
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-3.9.1.tar.gz",
        build_arguments=["--disable-documentation"],
        # build randomly fails with "*** missing separator.  Stop."
        build_parallel=False,
    ),
    Package(
        name="gnutls",
        requires=["nettle", "unistring"],
        source_url="https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.1.tar.xz",
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
        name="aom",
        requires=["cmake"],
        source_url="https://storage.googleapis.com/aom-releases/libaom-3.11.0.tar.gz",
        source_strip_components=1,
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
        requires=["meson", "nasm", "ninja"],
        source_url="https://code.videolan.org/videolan/dav1d/-/archive/1.4.1/dav1d-1.4.1.tar.bz2",
        build_system="meson",
    ),
    Package(
        name="libsvtav1",
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v2.2.1/SVT-AV1-v2.2.1.tar.gz",
        build_system="cmake",
    ),
    Package(
        name="lame",
        source_url="http://deb.debian.org/debian/pool/main/l/lame/lame_3.100.orig.tar.gz",
    ),
    Package(
        name="ogg",
        source_url="http://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.gz",
    ),
    Package(
        name="opus",
        source_url="https://github.com/xiph/opus/releases/download/v1.5.2/opus-1.5.2.tar.gz",
        build_arguments=["--disable-doc", "--disable-extra-programs"],
    ),
    Package(
        name="speex",
        source_url="http://downloads.xiph.org/releases/speex/speex-1.2.1.tar.gz",
        build_arguments=["--disable-binaries"],
    ),
    Package(
        name="twolame",
        source_url="http://deb.debian.org/debian/pool/main/t/twolame/twolame_0.4.0.orig.tar.gz",
        build_arguments=["--disable-sndfile"],
    ),
    Package(
        name="vorbis",
        requires=["ogg"],
        source_url="http://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.gz",
    ),
    Package(
        name="vpx",
        source_filename="vpx-1.14.0.tar.gz",
        source_url="https://github.com/webmproject/libvpx/archive/v1.14.0.tar.gz",
        build_arguments=[
            "--disable-examples",
            "--disable-tools",
            "--disable-unit-tests",
        ],
    ),
    Package(
        name="png",
        source_url="http://deb.debian.org/debian/pool/main/libp/libpng1.6/libpng1.6_1.6.45.orig.tar.gz",
        # avoid an assembler error on Windows
        build_arguments=["PNG_COPTS=-fno-asynchronous-unwind-tables"],
    ),
    Package(
        name="webp",
        source_filename="webp-1.5.0.tar.gz",
        source_url="https://github.com/webmproject/libwebp/archive/refs/tags/v1.5.0.tar.gz",
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
        name="opencore-amr",
        source_url="http://deb.debian.org/debian/pool/main/o/opencore-amr/opencore-amr_0.1.5.orig.tar.gz",
        # parallel build hangs on Windows
        build_parallel=plat != "Windows",
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/master/x264-master.tar.bz2",
        # parallel build runs out of memory on Windows
        build_parallel=plat != "Windows",
        gpl=True,
    ),
    Package(
        name="x265",
        requires=["cmake"],
        source_url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_3.5.tar.gz",
        build_system="cmake",
        source_dir="source",
        gpl=True,
    ),
    Package(
        name="srt",
        source_url="https://github.com/Haivision/srt/archive/refs/tags/v1.5.4.tar.gz",
        build_system="cmake",
        build_arguments =
            [r"-DOPENSSL_ROOT_DIR=C:\Program Files\OpenSSL"] if plat == "Windows"
            else ["-DENABLE_ENCRYPTION=OFF"] if plat == "Darwin"
            else [""]
            ),
]

openh264 = Package(
    name="openh264",
    requires=["meson", "nasm", "ninja"],
    source_filename="openh264-2.5.0.tar.gz",
    source_url="https://github.com/cisco/openh264/archive/refs/tags/v2.5.0.tar.gz",
    build_system="meson",
)

ffmpeg_package = Package(
    name="ffmpeg",
    source_url="https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz",
    build_arguments=[],
)


def download_tars(use_gnutls):
    # Try to download all tars at the start.
    # If there is an curl error, do nothing, then try again in `main()`

    local_libs = library_group
    if use_gnutls:
        local_libs += gnutls_group

    for package in local_libs + codec_group:
        tarball = os.path.join(
            os.path.abspath("source"),
            package.source_filename or package.source_url.split("/")[-1],
        )
        if not os.path.exists(tarball):
            try:
                fetch(package.source_url, tarball)
            except subprocess.CalledProcessError:
                pass


def main():
    global library_group

    parser = argparse.ArgumentParser("build-ffmpeg")
    parser.add_argument("destination")
    parser.add_argument("--enable-gpl", action="store_true")
    parser.add_argument("--disable-gpl", action="store_true")

    args = parser.parse_args()

    dest_dir = args.destination
    disable_gpl = args.disable_gpl
    del args

    output_dir = os.path.abspath("output")

    # FFmpeg has native TLS backends for macOS and Windows
    use_gnutls = plat == "Linux"

    if plat == "Linux" and os.environ.get("CIBUILDWHEEL") == "1":
        output_dir = "/output"
    output_tarball = os.path.join(output_dir, f"ffmpeg-{get_platform()}.tar.gz")

    if os.path.exists(output_tarball):
        return

    builder = Builder(dest_dir=dest_dir)
    builder.create_directories()

    download_tars(use_gnutls)

    # install packages
    available_tools = set()
    if plat == "Windows":
        available_tools.update(["gperf", "nasm"])

        # print tool locations
        print("PATH", os.environ["PATH"])
        for tool in ["gcc", "g++", "curl", "gperf", "ld", "nasm", "pkg-config"]:
            run(["where", tool])

    with log_group("install python packages"):
        run(["pip", "install", "cmake", "meson", "ninja"])

    # build tools
    if "gperf" not in available_tools:
        builder.build(
            Package(
                name="gperf",
                source_url="http://ftp.gnu.org/pub/gnu/gperf/gperf-3.1.tar.gz",
            ),
            for_builder=True,
        )

    if "nasm" not in available_tools:
        builder.build(
            Package(
                name="nasm",
                source_url="https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/nasm-2.14.02.tar.bz2",
            ),
            for_builder=True,
        )

    ffmpeg_package.build_arguments = [
        "--disable-alsa",
        "--disable-doc",
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
        "--enable-gmp",
        "--enable-gnutls" if use_gnutls else "--disable-gnutls",
        "--enable-libaom",
        "--enable-libdav1d",
        "--enable-libmp3lame",
        "--enable-libopencore-amrnb",
        "--enable-libopencore-amrwb",
        "--enable-libopus",
        "--enable-libspeex",
        "--enable-libsvtav1",
        "--enable-libsrt",
        "--enable-libtwolame",
        "--enable-libvorbis",
        "--enable-libvpx",
        "--enable-libwebp",
        "--enable-libxcb" if plat == "Linux" else "--disable-libxcb",
        "--enable-libxml2",
        "--enable-lzma",
        "--enable-zlib",
        "--enable-version3",
    ]
    if disable_gpl:
        ffmpeg_package.build_arguments.extend(
            ["--enable-libopenh264", "--disable-libx264"]
        )
    else:
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-libx264",
                "--disable-libopenh264",
                "--enable-libx265",
                "--enable-gpl",
            ]
        )
    if plat == "Darwin":
        ffmpeg_package.build_arguments.extend(
            ["--enable-videotoolbox", "--extra-ldflags=-Wl,-ld_classic"]
        )

    if use_gnutls:
        library_group += gnutls_group

    package_groups = [library_group + codec_group, [ffmpeg_package]]
    packages = [p for p_list in package_groups for p in p_list]

    for package in packages:
        if disable_gpl and package.gpl:
            if package.name == "x264":
                builder.build(openh264)
            else:
                pass
        else:
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
