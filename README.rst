pyav-ffmpeg
===========

This project provides binary builds of FFmpeg and its dependencies for `PyAV`_.
These builds are used in order to provide binary wheels of PyAV, allowing
users to easily install PyAV without perform error-prone compilations.

The builds are provided for several platforms:

- Linux (x86_64, aarch64) 
- macOS (x86_64, arm64)
- Windows (x86_64)

Features
--------

Currently FFmpeg 8.0.1 is built with the following packages enabled for all platforms:

- gmp 6.3.0
- aom 3.13.3
- dav1d 1.5.2
- libsvtav1 3.1.0
- lame 3.100
- ogg 1.3.5
- opus 1.6
- speex 1.2.1
- twolame 0.4.0
- vorbis 1.3.7
- vpx 1.15.1
- png 1.6.47
- webp 1.5.0
- openh264 2.6.0
- opencore-amr 0.1.5
- x264 32c3b801191522961102d4bea292cdb61068d0dd
- x265 4.1

The following additional packages are also enabled on Linux:

- gnutls 3.8.9
- nettle 3.10.1
- unistring 1.3

.. _PyAV: https://github.com/PyAV-Org/PyAV
