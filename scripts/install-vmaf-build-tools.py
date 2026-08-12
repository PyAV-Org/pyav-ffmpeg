import shutil
import subprocess


def main() -> None:
    if shutil.which("xxd"):
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

    if not shutil.which("xxd"):
        raise RuntimeError("xxd is unavailable after package installation")


if __name__ == "__main__":
    main()