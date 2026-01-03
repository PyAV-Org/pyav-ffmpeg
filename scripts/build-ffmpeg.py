import argparse
import concurrent.futures
import glob
import hashlib
import os
import platform
import shutil
import subprocess

from cibuildpkg import Builder, Package, When, fetch, get_platform, log_group, run

plat = platform.system()
is_musllinux = plat == "Linux" and platform.libc_ver()[0] != "glibc"


def calculate_sha256(filename: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


library_group = [
    Package(
        name="gmp",
        source_url="https://ftp.gnu.org/gnu/gmp/gmp-6.3.0.tar.xz",
        sha256="a3c2b80201b89e68616f4ad30bc66aee4927c3ce50e33929ca819d5c43538898",
        # out-of-tree builds fail on Windows
        build_dir=".",
    ),
]

gnutls_group = [
    Package(
        name="unistring",
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.3.tar.gz",
        sha256="8ea8ccf86c09dd801c8cac19878e804e54f707cf69884371130d20bde68386b7",
    ),
    Package(
        name="nettle",
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-3.10.1.tar.gz",
        sha256="b0fcdd7fc0cdea6e80dcf1dd85ba794af0d5b4a57e26397eee3bc193272d9132",
        requires=["gmp"],
        build_arguments=["--disable-documentation"],
        # build randomly fails with "*** missing separator.  Stop."
        build_parallel=False,
    ),
    Package(
        name="gnutls",
        source_url="https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.9.tar.xz",
        sha256="69e113d802d1670c4d5ac1b99040b1f2d5c7c05daec5003813c049b5184820ed",
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
        name="aom",
        source_url="https://storage.googleapis.com/aom-releases/libaom-3.13.1.tar.gz",
        sha256="19e45a5a7192d690565229983dad900e76b513a02306c12053fb9a262cbeca7d",
        requires=["cmake"],
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
        source_url="https://code.videolan.org/videolan/dav1d/-/archive/1.5.2/dav1d-1.5.2.tar.bz2",
        sha256="c748a3214cf02a6d23bc179a0e8caea9d6ece1e46314ef21f5508ca6b5de6262",
        requires=["meson", "nasm", "ninja"],
        build_system="meson",
    ),
    Package(
        name="libsvtav1",
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v3.1.0/SVT-AV1-v3.1.0.tar.bz2",
        sha256="8231b63ea6c50bae46a019908786ebfa2696e5743487270538f3c25fddfa215a",
        build_system="cmake",
    ),
    Package(
        name="lame",
        source_url="http://deb.debian.org/debian/pool/main/l/lame/lame_3.100.orig.tar.gz",
        sha256="ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e",
    ),
    Package(
        name="ogg",
        source_url="http://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.gz",
        sha256="0eb4b4b9420a0f51db142ba3f9c64b333f826532dc0f48c6410ae51f4799b664",
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
        name="twolame",
        source_url="http://deb.debian.org/debian/pool/main/t/twolame/twolame_0.4.0.orig.tar.gz",
        sha256="cc35424f6019a88c6f52570b63e1baf50f62963a3eac52a03a800bb070d7c87d",
        build_arguments=["--disable-sndfile"],
    ),
    Package(
        name="vorbis",
        source_url="https://ftp.osuosl.org/pub/xiph/releases/vorbis/libvorbis-1.3.7.tar.xz",
        sha256="b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b",
        requires=["ogg"],
    ),
    Package(
        name="vpx",
        source_url="https://github.com/webmproject/libvpx/archive/v1.15.1.tar.gz",
        sha256="6cba661b22a552bad729bd2b52df5f0d57d14b9789219d46d38f73c821d3a990",
        source_filename="vpx-1.15.1.tar.gz",
        build_arguments=[
            "--disable-examples",
            "--disable-tools",
            "--disable-unit-tests",
        ],
    ),
    Package(
        name="png",
        source_url="https://download.sourceforge.net/libpng/libpng-1.6.47.tar.gz",
        sha256="084115c62fe023e3d88cd78764a4d8e89763985ee4b4a085825f7a00d85eafbb",
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
        requires=["meson", "ninja"],
        build_system="meson",
    ),
    Package(
        name="fdk_aac",
        source_url="https://github.com/mstorsjo/fdk-aac/archive/refs/tags/v2.0.3.tar.gz",
        sha256="e25671cd96b10bad896aa42ab91a695a9e573395262baed4e4a2ff178d6a3a78",
        when=When.commercial_only,
        build_system="cmake",
    ),
    Package(
        name="opencore-amr",
        source_url="http://deb.debian.org/debian/pool/main/o/opencore-amr/opencore-amr_0.1.5.orig.tar.gz",
        sha256="2c006cb9d5f651bfb5e60156dbff6af3c9d35c7bbcc9015308c0aff1e14cd341",
        # parallel build hangs on Windows
        build_parallel=plat != "Windows",
        when=When.community_only,
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/32c3b801191522961102d4bea292cdb61068d0dd/x264-32c3b801191522961102d4bea292cdb61068d0dd.tar.bz2",
        sha256="d7748f350127cea138ad97479c385c9a35a6f8527bc6ef7a52236777cf30b839",
        # assembly contains textrels which are not supported by musl
        build_arguments=["--disable-asm"] if is_musllinux else [],
        # parallel build runs out of memory on Windows
        build_parallel=plat != "Windows",
        when=When.community_only,
    ),
    Package(
        name="x265",
        source_url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_4.1.tar.gz",
        sha256="a31699c6a89806b74b0151e5e6a7df65de4b49050482fe5ebf8a4379d7af8f29",
        build_system="cmake",
        source_dir="source",
        when=When.community_only,
    ),
    # Package(
    #     name="srt",
    #     source_url="https://github.com/Haivision/srt/archive/refs/tags/v1.5.4.tar.gz",
    #     sha256="d0a8b600fe1b4eaaf6277530e3cfc8f15b8ce4035f16af4a5eb5d4b123640cdd",
    #     build_system="cmake",
    #     build_arguments=(
    #         [r"-DOPENSSL_ROOT_DIR=C:\Program Files\OpenSSL"]
    #         if plat == "Windows"
    #         else ["-DENABLE_ENCRYPTION=OFF"]
    #         if plat == "Darwin"
    #         else [""]
    #     ),
    #     when=When.community_only,
    # ),
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
    requires=["cmake"],
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
    output_tarball = os.path.join(output_dir, f"ffmpeg-{get_platform()}.tar.gz")

    if os.path.exists(output_tarball):
        return

    builder = Builder(dest_dir=dest_dir)
    builder.create_directories()

    # install packages
    available_tools = set()
    if plat == "Windows":
        available_tools.update(["gperf", "nasm"])

        # print tool locations
        print("PATH", os.environ["PATH"])
        for tool in ["gcc", "g++", "curl", "gperf", "ld", "nasm", "pkg-config"]:
            run(["where", tool])

    with log_group("install python packages"):
        run(["pip", "install", "cmake==3.31.6", "meson", "ninja"])

    # build tools
    build_tools = []
    if "gperf" not in available_tools:
        build_tools.append(
            Package(
                name="gperf",
                source_url="http://ftp.gnu.org/pub/gnu/gperf/gperf-3.1.tar.gz",
                sha256="588546b945bba4b70b6a3a616e80b4ab466e3f33024a352fc2198112cdbb3ae2",
            )
        )

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
        "--enable-gmp",
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
        # "--enable-libsrt" if community else "--disable-libsrt",
        "--enable-libtwolame",
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

    if not community:
        ffmpeg_package.build_arguments.append("--enable-libfdk_aac")

    if plat == "Darwin":
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-videotoolbox",
                "--enable-audiotoolbox",
                "--extra-ldflags=-Wl,-ld_classic",
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

    packages = library_group[:]
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
