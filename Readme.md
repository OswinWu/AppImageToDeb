# AppImage to .deb Converter

A powerful Python script to convert an AppImage file into a fully-featured, system-integrated Debian (`.deb`) package.

While AppImage files offer excellent portability, they often lack proper integration with the host system. This script bridges that gap. After installing the `.deb` package it generates, your application will:

*   Appear in your application menu with the correct icon.
*   Be launchable directly from the terminal by typing its name.
*   Be manageable (install, upgrade, remove) through your system's package manager like `apt`.

## ✨ Features

*   **Automatic Metadata Extraction**: Intelligently extracts the application name, version, icon, and description from the `.desktop` file inside the AppImage.
*   **Proper Installation Paths**: Installs the AppImage file to `/usr/lib/<package-name>/`, adhering to Linux Filesystem Hierarchy Standards.
*   **Command-Line Launcher**: Creates a symbolic link in `/usr/bin/`, allowing you to run the application directly from your terminal.
*   **Desktop & Icon Integration**: Finds the best icon, installs it to `/usr/share/icons/`, and modifies the `.desktop` file to ensure it displays correctly in your application menu.
*   **Dependency Management**: Includes essential dependencies for running AppImages (like `libfuse2`) by default and allows for easy customization.
*   **Highly Customizable**: Provides a rich set of command-line options to override any auto-detected package information (name, version, maintainer, etc.).
*   **Robust Packaging Process**: Uses `fakeroot` and `dpkg-deb` to build the package, ensuring correct file permissions and ownership.

## ⚙️ Prerequisites

Before running this script, ensure your Debian-based system (Debian, Ubuntu, Linux Mint, etc.) has the following tools installed:

*   Python 3
*   `dpkg-deb` (from the `dpkg-dev` package)
*   `fakeroot`
*   `libfuse2` or `fuse` (required by most AppImages)

You can install all dependencies with a single command:

```bash
sudo apt update
sudo apt install python3 dpkg-dev fakeroot libfuse2
```

## 🚀 How to Use

1.  **Save the Script**: Save the Python code to a file, for example, `appimage2deb.py`.

2.  **Make it Executable**: In your terminal, grant execution permissions to the script:

    ```bash
    chmod +x appimage2deb.py
    ```

3.  **Run the Script**:

    *   **Basic Usage** (with automatic detection):

        ```bash
        ./appimage2deb.py /path/to/YourApplication.AppImage
        ```
        This will create a `.deb` file in the current directory.

    *   **Advanced Usage** (customizing package info):

        ```bash
        ./appimage2deb.py YourApp-1.2.3.AppImage -n my-cool-app -v 1.2.3 -m "Your Name <you@email.com>" -o ./packages
        ```
        This command will:
        *   Set the package name to `my-cool-app`.
        *   Set the version to `1.2.3`.
        *   Set the maintainer information.
        *   Output the final `.deb` file to the `./packages` directory.

## 📋 Command-Line Options

| Short  | Long            | Description                                                    | Default                                             |
| :----- | :-------------- | :------------------------------------------------------------- | :-------------------------------------------------- |
| (none) | `appimage_path` | **[Required]** Path to the AppImage file.                      | (none)                                              |
| `-o`   | `--output-dir`  | Output directory for the generated `.deb` file.                | Current directory                                   |
| `-n`   | `--name`        | Override the auto-detected package name.                       | Derived from the `.desktop` filename                |
| `-v`   | `--version`     | Override the auto-detected version number.                     | Extracted from `X-AppImage-Version` field           |
| `-m`   | `--maintainer`  | The maintainer information for the package.                    | The current user                                    |
| `-w`   | `--homepage`    | The homepage URL for the application.                          | `https://example.com`                               |
| `-d`   | `--description` | The short description (shown in `apt` lists).                  | Extracted from the `Name` field in the `.desktop` file |
| `-l`   | `--long-desc`   | The long, detailed description.                                | "This package provides..."                        |
| `-s`   | `--section`     | The package section (e.g., `graphics`, `network`, `utils`).    | `misc`                                              |
| `-p`   | `--priority`    | The package priority (e.g., `optional`, `required`).           | `optional`                                          |
| `-D`   | `--depends`     | Customize the package dependencies.                            | `libc6 (>= 2.31), libfuse2 \| fuse`                 |

## 🔬 How It Works

The script follows these steps to convert an AppImage into a compliant Debian package:

1.  **Extract**: Uses the `--appimage-extract` command to unpack the AppImage into a temporary directory.
2.  **Parse**: Scans the extracted contents to find the `.desktop` file and associated icon files to gather metadata.
3.  **Create Structure**: Builds a standard Debian package directory structure (e.g., `DEBIAN/`, `usr/bin/`, `usr/lib/`, `usr/share/applications/`) in a temporary staging area.
4.  **Place Files**:
    *   Copies the **original AppImage file** to `/usr/lib/<package-name>/`.
    *   Creates a **symbolic link** in `/usr/bin/` that points to the AppImage, creating the command-line launcher.
    *   Copies the found **icon file** to `/usr/share/icons/hicolor/scalable/apps/`.
    *   **Modifies and saves the `.desktop` file** to `/usr/share/applications/`, ensuring the `Exec=` and `Icon=` fields point to the new launcher and icon.
5.  **Generate Control Files**: Creates the `DEBIAN/control` file based on the extracted and user-provided arguments. It also creates a `DEBIAN/postinst` script to update the desktop and icon caches upon installation.
6.  **Build Package**: Invokes `fakeroot dpkg-deb --build` to compile the staging directory into the final `.deb` file.
7.  **Clean Up**: Deletes all temporary directories and files.