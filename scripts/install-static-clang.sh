#!/bin/bash

# Stop at any error, show all commands
set -exuo pipefail

TOOLCHAIN_PATH=/opt/clang

# Download static-clang
DEFAULT_ARCH="$(uname -m)"
if [ "${STATIC_CLANG_ARCH:-}" == "" ]; then
	STATIC_CLANG_ARCH="${RUNNER_ARCH:-${DEFAULT_ARCH}}"
fi
case "${STATIC_CLANG_ARCH}" in
	ARM64|aarch64|arm64|arm64/*) GO_ARCH=arm64;;
	ARM|armv7l|armv8l|arm|arm/v7) GO_ARCH=arm;;  # assume arm/v7 for arm
	X64|x86_64|amd64|amd64/*) GO_ARCH=amd64;;
	X86|i686|386) GO_ARCH=386;;
	ppc64le) GO_ARCH=ppc64le;;
	riscv64) GO_ARCH=riscv64;;
	s390x) GO_ARCH=s390x;;
	*) echo "No static-clang toolchain for ${CLANG_ARCH}">2; exit 1;;
esac
STATIC_CLANG_VERSION=23.1.4.0
STATIC_CLANG_FILENAME="static-clang-linux-${GO_ARCH}.tar.xz"
STATIC_CLANG_URL="https://github.com/mayeut/static-clang-images/releases/download/v${STATIC_CLANG_VERSION}/${STATIC_CLANG_FILENAME}"
pushd /tmp
cat<<'EOF' | grep "${STATIC_CLANG_FILENAME}" > "${STATIC_CLANG_FILENAME}.sha256"
4070a2a3342eb93fcc686b974dcd663490bbe8da01c082924cce6e07675bcc85  static-clang-linux-386.tar.xz
6580146eab36228d9e10dbf280a67adb11ce5d4b0275ac14302fcbf4f722e2a3  static-clang-linux-amd64.tar.xz
41ecc4bda79a3db83fe6f1b719f368b201ed0ced614856c3ce32fa3f031ed6bf  static-clang-linux-arm.tar.xz
501b34ca9d21bfa08a40d99eb5bd06664f6209a244bb2d52f007ad6fec977623  static-clang-linux-arm64.tar.xz
cc45b104c92201361446e20794c59011b4f9005f3601354b31f22ff4414e79f1  static-clang-linux-loong64.tar.xz
88097702c270ad3646ad47f90ad9d77b48aa321e04b33a24120d7b7ccbfdc927  static-clang-linux-ppc64le.tar.xz
775437eb73958e24328f36135f92cbe3db964771e5bd0354b0f1cffa5c784798  static-clang-linux-riscv64.tar.xz
1004c314ce1e0a14c216df0d350c8e5da3978085f269c8ee6cee03354b78c0d9  static-clang-linux-s390x.tar.xz
EOF
curl -fsSLO "${STATIC_CLANG_URL}"
sha256sum -c "${STATIC_CLANG_FILENAME}.sha256"
tar -C /opt -xf "${STATIC_CLANG_FILENAME}"
popd

# configure target triple
case "${AUDITWHEEL_POLICY}-${AUDITWHEEL_ARCH}" in
	manylinux*-armv7l) TARGET_TRIPLE=armv7-unknown-linux-gnueabihf;;
	musllinux*-armv7l) TARGET_TRIPLE=armv7-alpine-linux-musleabihf;;
	manylinux*-ppc64le) TARGET_TRIPLE=powerpc64le-unknown-linux-gnu;;
	musllinux*-ppc64le) TARGET_TRIPLE=powerpc64le-alpine-linux-musl;;
	manylinux*-*) TARGET_TRIPLE=${AUDITWHEEL_ARCH}-unknown-linux-gnu;;
	musllinux*-*) TARGET_TRIPLE=${AUDITWHEEL_ARCH}-alpine-linux-musl;;
esac
case "${AUDITWHEEL_POLICY}-${AUDITWHEEL_ARCH}" in
	*-riscv64) M_ARCH="-march=rv64gc";;
	*-x86_64) M_ARCH="-march=x86-64";;
	*-armv7l) M_ARCH="-march=armv7-a -mfpu=neon-vfpv3 -mfloat-abi=hard";;
	manylinux*-i686) M_ARCH="-march=k8 -mtune=generic";;  # same as gcc manylinux2014 / manylinux_2_28
	musllinux*-i686) M_ARCH="-march=pentium-m -mtune=generic";;  # same as gcc musllinux_1_2
esac
GCC_TRIPLE=$(gcc -dumpmachine)

cat<<EOF >"${TOOLCHAIN_PATH}/bin/${AUDITWHEEL_PLAT}.cfg"
	-target ${TARGET_TRIPLE}
	${M_ARCH:-}
	--gcc-toolchain=${DEVTOOLSET_ROOTPATH:-}/usr
	--gcc-triple=${GCC_TRIPLE}
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang++.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang-cpp.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

# override entrypoint to add the toolchain to PATH
mv /usr/local/bin/manylinux-entrypoint /usr/local/bin/manylinux-entrypoint-org
cat<<EOF >/usr/local/bin/manylinux-entrypoint
#!/bin/bash

set -eu

export PATH="${TOOLCHAIN_PATH}/bin:\${PATH}"
exec /usr/local/bin/manylinux-entrypoint-org "\$@"
EOF

chmod +x /usr/local/bin/manylinux-entrypoint
