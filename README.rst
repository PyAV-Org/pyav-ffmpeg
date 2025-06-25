pyav-ffmpeg
===========

This project provides binary builds of FFmpeg and its dependencies for `PyAV`_.
These builds are used in order to provide binary wheels of PyAV, allowing
users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, i686, aarch64)
- macOS (x86_64, arm64)
- Windows (AMD64)

Features
--------

Currently FFmpeg 7.1.1 is built with the following packages enabled for all platforms:

- gmp 6.3.0
- aom 3.11.0
- dav1d 1.4.1
- lame 3.100
- ogg 1.3.5
- opencore-amr 0.1.5
- openh264 2.6.0
- opus 1.5.2
- speex 1.2.1
- svt-av1 3.0.1
- srt 1.5.4 (encryption disabled on macOS)
- twolame 0.4.0
- vorbis 1.3.7
- vpx 1.15.1
- png 1.6.47
- webp 1.5.0
- x264 master
- x265 3.5

The following additional packages are also enabled on Linux:

- gnutls 3.8.9
- nettle 3.10.1
- unistring 1.3

.. _PyAV: https://github.com/PyAV-Org/PyAV
