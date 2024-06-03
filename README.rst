pyav-ffmpeg
===========

This project provides binary builds of FFmpeg and its dependencies for `PyAV`_.
These builds are used in order to provide binary wheels of PyAV, allowing
users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, i686, aarch64, ppc64le)
- macOS (x86_64, arm64)
- Windows (AMD64)

Features
--------

Currently FFmpeg 6.1.1 is built with the following packages enabled for all platforms:

- fontconfig 2.15.0
- freetype 2.10.1
- fribidi 1.0.11
- gmp 6.3.0
- harfbuzz 4.1.0
- png 1.6.37
- xml2 2.9.13
- xz 5.4.4
- aom 3.2.0
- ass 0.15.2
- bluray 1.3.4
- dav1d 1.4.1
- lame 3.100
- ogg 1.3.5
- opencore-amr 0.1.5
- openjpeg 2.5.2
- opus 1.4
- speex 1.2.1
- twolame 0.4.0
- vorbis 1.3.7
- vpx 1.14.0
- webp 1.4.0
- x264 master
- x265 3.5
- xvid 1.3.7

The following additional packages are also enabled on Linux:

- gnutls 3.8.1
- nettle 3.9.1
- unistring 1.2

.. _PyAV: https://github.com/PyAV-Org/PyAV
