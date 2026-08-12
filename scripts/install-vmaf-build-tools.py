import os
import shutil
import subprocess
import tempfile


def xxd_supports_model_embedding() -> bool:
    xxd = shutil.which("xxd")
    if xxd is None:
        return False

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input")
        output_path = os.path.join(temp_dir, "output.c")
        with open(input_path, "wb") as input_file:
            input_file.write(b"vmaf")
        result = subprocess.run(
            [xxd, "-i", input_path, output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return (
            result.returncode == 0
            and os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
        )


def main() -> None:
    if xxd_supports_model_embedding():
        return

    if shutil.which("apt-get"):
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "xxd"], check=True)
    else:
        package_commands = (
            ("apk", ["apk", "add", "--no-cache", "xxd"]),
            ("dnf", ["dnf", "install", "-y", "vim-common"]),
            ("yum", ["yum", "install", "-y", "vim-common"]),
        )
        for package_manager, command in package_commands:
            if shutil.which(package_manager):
                subprocess.run(command, check=True)
                break
        else:
            raise RuntimeError("Unable to install xxd for VMAF model embedding")

    if not xxd_supports_model_embedding():
        raise RuntimeError("xxd does not support VMAF model embedding")


if __name__ == "__main__":
    main()