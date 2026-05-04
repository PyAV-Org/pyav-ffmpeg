from pkg import all_packages

def main():
    with open("cache.txt", "w") as file:
        for package in sorted(all_packages):
            file.write(f"{package.name}:{package.sha256}\n")

if __name__ == "__main__":
    main()

