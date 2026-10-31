# pyav-ffmpeg

This project provides binary builds of FFmpeg and its dependencies for [PyAV](https://github.com/PyAV-Org/PyAV). These builds are used in order to provide binary wheels of PyAV, allowing users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, aarch64, armv7l, ppc64le, riscv64)
- macOS (x86_64, arm64)
- Windows (x86_64, aarch64)

Features
--------

Currently FFmpeg 9.0.2 is built with the following packages enabled for all platforms:

- [bwlame](https://github.com/basswood-io/bwlame) 4.1.0
- opus 1.6.1
- dav1d 1.5.4
- libsvtav1 4.2.0
- vpx 1.17.0
- webp 1.6.0
- libvmaf 3.2.1
- x264 b35605ace3ddf7c1a5d67a2eb553f034aef41d55 (except armv7l)
- x265 4.3
- freetype 2.15.0
- fribidi 1.0.17
- harfbuzz 15.0.0
- libunibreak 8.0
- libass 0.17.5

The following additional packages are also enabled on Linux:

- gnutls 3.8.13
- nettle 4.0
- unistring 1.5
