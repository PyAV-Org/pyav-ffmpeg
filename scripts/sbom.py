import importlib

# Equivalent to: from 'build-ffmpeg' import *
build_ffmpeg = importlib.import_module("build-ffmpeg")
globals().update(
    {k: getattr(build_ffmpeg, k) for k in dir(build_ffmpeg) if not k.startswith("_")}
)


def get_version(package):
    def get_name(url):
        if url.startswith("https://github.com"):
            return url[url.rindex("/") + 1 :]

        try:
            return url[url.rindex("-") + 1 :]
        except ValueError:
            try:
                return url[url.rindex("_") + 1 :]
            except ValueError:
                return url

    version = get_name(package.source_url)

    if version.startswith("v"):
        version = version[1:]
    if "-" in version:
        version = version[version.index("-") + 1 :]
    if "_" in version:
        version = version[version.index("_") + 1 :]

    if ".orig" in version:
        return version[: version.rindex(".orig")]
    if ".tar" in version:
        return version[: version.rindex(".tar")]
    return version


def main():
    print(
        f"Currently FFmpeg {get_version(ffmpeg_package)} is built with the following packages enabled for all platforms:\n"
    )

    for package in codec_group:
        print(f"- {package.name} {get_version(package)}")

    print("\nThe following additional packages are also enabled on Linux:\n")
    for package in sorted(gnutls_group):
        print(f"- {package.name} {get_version(package)}")
    print()


if __name__ == "__main__":
    main()
