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
        name="xz",
        source_url="https://github.com/tukaani-project/xz/releases/download/v5.6.3/xz-5.6.3.tar.xz",
        sha256="db0590629b6f0fa36e74aea5f9731dc6f8df068ce7b7bafa45301832a5eebc3a",
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
        sha256="a3c2b80201b89e68616f4ad30bc66aee4927c3ce50e33929ca819d5c43538898",
        # out-of-tree builds fail on Windows
        build_dir=".",
    ),
    Package(
        name="xml2",
        source_url="https://download.gnome.org/sources/libxml2/2.14/libxml2-2.14.3.tar.xz",
        sha256="6de55cacc8c2bc758f2ef6f93c313cb30e4dd5d84ac5d3c7ccbd9344d8cc6833",
        requires=["xz"],
        build_arguments=["--without-python"],
    ),
]

gnutls_group = [
    Package(
        name="unistring",
        source_url="https://ftp.gnu.org/gnu/libunistring/libunistring-1.2.tar.gz",
        sha256="fd6d5662fa706487c48349a758b57bc149ce94ec6c30624ec9fdc473ceabbc8e",
    ),
    Package(
        name="nettle",
        source_url="https://ftp.gnu.org/gnu/nettle/nettle-3.9.1.tar.gz",
        sha256="ccfeff981b0ca71bbd6fbcb054f407c60ffb644389a5be80d6716d5b550c6ce3",
        requires=["gmp"],
        build_arguments=["--disable-documentation"],
        # build randomly fails with "*** missing separator.  Stop."
        build_parallel=False,
    ),
    Package(
        name="gnutls",
        source_url="https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.1.tar.xz",
        sha256="ba8b9e15ae20aba88f44661978f5b5863494316fe7e722ede9d069fe6294829c",
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
        source_url="https://storage.googleapis.com/aom-releases/libaom-3.11.0.tar.gz",
        sha256="cf7d103d2798e512aca9c6e7353d7ebf8967ee96fffe9946e015bb9947903e3e",
        requires=["cmake"],
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
        source_url="https://code.videolan.org/videolan/dav1d/-/archive/1.4.1/dav1d-1.4.1.tar.bz2",
        sha256="ab02c6c72c69b2b24726251f028b7cb57d5b3659eeec9f67f6cecb2322b127d8",
        requires=["meson", "nasm", "ninja"],
        build_system="meson",
    ),
    Package(
        name="libsvtav1",
        source_url="https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v3.0.1/SVT-AV1-v3.0.1.tar.bz2",
        sha256="f1d1ad8db551cd84ab52ae579b0e5086d8a0b7e47aea440e75907242a51b4cb9",
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
        source_url="https://github.com/xiph/opus/releases/download/v1.5.2/opus-1.5.2.tar.gz",
        sha256="65c1d2f78b9f2fb20082c38cbe47c951ad5839345876e46941612ee87f9a7ce1",
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
        when=When.commercial_only,
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
        # parallel build hangs on Windows
        build_parallel=plat != "Windows",
        when=When.community_only,
    ),
    Package(
        name="x264",
        source_url="https://code.videolan.org/videolan/x264/-/archive/master/x264-master.tar.bz2",
        # assembly contains textrels which are not supported by musl
        build_arguments=["--disable-asm"] if is_musllinux else [],
        # parallel build runs out of memory on Windows
        build_parallel=plat != "Windows",
        when=When.community_only,
    ),
    Package(
        name="x265",
        source_url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_3.5.tar.gz",
        build_system="cmake",
        source_dir="source",
        when=When.community_only,
    ),
    Package(
        name="srt",
        source_url="https://github.com/Haivision/srt/archive/refs/tags/v1.5.4.tar.gz",
        build_system="cmake",
        build_arguments=(
            [r"-DOPENSSL_ROOT_DIR=C:\Program Files\OpenSSL"]
            if plat == "Windows"
            else ["-DENABLE_ENCRYPTION=OFF"]
            if plat == "Darwin"
            else [""]
        ),
        when=When.community_only,
    ),
]

nvheaders = Package(
    name="nv-codec-headers",
    source_url="https://github.com/FFmpeg/nv-codec-headers/archive/refs/tags/n13.0.19.0.tar.gz",
    sha256="86d15d1a7c0ac73a0eafdfc57bebfeba7da8264595bf531cf4d8db1c22940116",
    build_system="make",
)

ffmpeg_package = Package(
    name="ffmpeg",
    source_url="https://ffmpeg.org/releases/ffmpeg-7.1.1.tar.xz",
    sha256="733984395e0dbbe5c046abda2dc49a5544e7e0e1e2366bba849222ae9e3a03b1",
    build_arguments=[],
    build_parallel=plat != "Windows",
)


def download_and_verify_package(package: Package) -> tuple[str, str]:
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
    if package.sha256 is None:
        print(f"sha256 for {package.name}: {sha}")
    elif package.sha256 == sha:
        print(f"{package.name} tarball: hashes match")
    else:
        raise ValueError(
            f"sha256 hash of {package.name} tarball do not match!\nExpected: {package.sha}\nGot: {sha}"
        )

    return package.name, tarball


def download_tars(packages: list[Package]) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_package = {
            executor.submit(download_and_verify_package, package): package.name
            for package in packages
        }

        for future in concurrent.futures.as_completed(future_to_package):
            try:
                name, tarball = future.result()
            except Exception as exc:
                print(f"{name} generated an exception: {exc}")
                raise


def main():
    global library_group

    parser = argparse.ArgumentParser("build-ffmpeg")
    parser.add_argument("destination")
    parser.add_argument("--community", action="store_true")
    parser.add_argument("--commercial", action="store_true")
    parser.add_argument(
        "--enable-cuda", action="store_true", help="Enable NVIDIA CUDA support"
    )

    args = parser.parse_args()

    if args.community and args.commercial:
        raise ValueError("mutually exclusive")

    dest_dir = args.destination
    community = args.community
    enable_cuda = args.enable_cuda and plat in {"Linux", "Windows"}
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

    # Fix winpthreads breakage until the fix reaches msys2 repos.
    if plat == "Windows":
        run(["patch", "-d", "C:/msys64/mingw64", "-i", os.path.join(builder.patch_dir, "winpthreads.patch"), "-p3"])

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
                source_url="https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/nasm-2.14.02.tar.bz2",
                sha256="34fd26c70a277a9fdd54cb5ecf389badedaf48047b269d1008fbc819b24e80bc",
            )
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
        "--enable-libopencore-amrnb" if community else "--disable-libopencore-amrnb",
        "--enable-libopencore-amrwb" if community else "--disable-libopencore-amrwb",
        "--enable-libopus",
        "--enable-libspeex",
        "--enable-libsvtav1",
        "--enable-libsrt" if community else "--disable-libsrt",
        "--enable-libtwolame",
        "--enable-libvorbis",
        "--enable-libvpx",
        "--enable-libwebp",
        "--enable-libxcb" if plat == "Linux" else "--disable-libxcb",
        "--enable-libxml2" if community else "--disable-libxml2",
        "--enable-lzma",
        "--enable-zlib",
        "--enable-version3",
    ]

    if enable_cuda:
        ffmpeg_package.build_arguments.extend(["--enable-nvenc", "--enable-nvdec"])

    if community:
        ffmpeg_package.build_arguments.extend(
            [
                "--enable-libx264",
                "--disable-libopenh264",
                "--enable-gpl",
            ]
        )
    else:
        ffmpeg_package.build_arguments.extend(
            ["--enable-libopenh264", "--disable-libx264", "--enable-libfdk_aac"]
        )

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

    if use_gnutls:
        library_group += gnutls_group
    if enable_cuda:
        library_group += [nvheaders]

    package_groups = [library_group + codec_group, [ffmpeg_package]]
    packages = [p for p_list in package_groups for p in p_list]

    filtered_packages = []

    for package in packages:
        if package.when == When.never:
            continue
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
