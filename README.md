# pyav-ffmpeg

This project provides binary builds of FFmpeg and its dependencies for [PyAV](https://github.com/PyAV-Org/PyAV). These builds are used in order to provide binary wheels of PyAV, allowing users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, aarch64, armv7l, ppc64le, riscv64)
- macOS (x86_64, arm64)
- Windows (x86_64, aarch64)

Features
--------

Currently FFmpeg 8.1.2 is built with the following packages enabled for all platforms:

- [lamer](https://github.com/basswood-io/lamer) 3.101.0
- opus 1.6.1
- dav1d 1.5.4
- libsvtav1 4.2.0
- vpx 1.16.0
- png 1.6.58
- webp 1.6.0
- opencore-amr 0.1.6
- x264 32c3b801191522961102d4bea292cdb61068d0dd (except armv7l)
- x265 4.2 (except armv7l)

The following additional packages are also enabled on Linux:

- gnutls 3.8.13
- nettle 3.10.2
- unistring 1.4.2
