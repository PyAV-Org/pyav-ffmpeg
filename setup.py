import setuptools
import sys

if sys.platform == "win32":
    include_dirs = ["C:\\cibw\\vendor\\include"]
    library_dirs = ["C:\\cibw\\vendor\\lib"]
    extra_link_args = []
else:
    include_dirs = ["/tmp/vendor/include"]
    library_dirs = ["/tmp/vendor/lib"]
    extra_link_args = ["-headerpad_max_install_names"] if sys.platform == "darwin" else []

setuptools.setup(
    name="dummy",
    package_dir={"": "src"},
    packages=["dummy"],
    ext_modules=[
        setuptools.Extension(
            "dummy.binding",
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            extra_link_args=extra_link_args,
            libraries=[
                "avformat",
                "avcodec",
                "avdevice",
                "avutil",
                "avfilter",
                "swscale",
                "swresample",
            ],
            sources=["src/dummy/binding.c"],
        ),
    ],
)
