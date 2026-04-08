pyav-ffmpeg
===========

This project provides binary builds of FFmpeg and its dependencies for `PyAV`_.
These builds are used in order to provide binary wheels of PyAV, allowing
users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, aarch64, ppc64le, riscv64)
- macOS (x86_64, arm64)
- Windows (x86_64, aarch64)

Features
--------

Currently FFmpeg 8.1 is built with the following packages enabled for all platforms:

- lame 3.100
- ogg 1.3.6
- opus 1.6.1
- vorbis 1.3.7
- dav1d 1.5.3
- libsvtav1 4.0.1
- vpx 1.16.0
- png 1.6.56
- webp 1.5.0
- openh264 2.6.0
- opencore-amr 0.1.6
- x264 32c3b801191522961102d4bea292cdb61068d0dd
- x265 4.1

The following additional packages are also enabled on Linux:

- gnutls 3.8.11
- nettle 3.10.2
- unistring 1.4.1

.. _PyAV: https://github.com/PyAV-Org/PyAV
