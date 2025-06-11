# AppImage to .deb Converter

这是一个强大的Python脚本，用于将 AppImage 文件转换为功能齐全、系统集成的 Debian (`.deb`) 软件包。

传统的AppImage文件提供了极佳的便携性，但它们通常无法与系统很好地集成。此脚本解决了这个问题，它生成的`.deb`包在安装后，你的应用程序将：

*   出现在应用程序菜单中（带有正确的图标）。
*   可以通过在终端中输入其名称来直接执行。
*   可以通过系统的包管理器（如 `apt`）进行管理、升级或卸载。

## ✨ 功能特性

*   **自动元数据提取**: 自动从AppImage内部的 `.desktop` 文件中提取应用程序名称、版本、图标和描述。
*   **正确的安装路径**: 将AppImage文件本身安装到 `/usr/lib/<包名>/`，遵循Linux文件系统标准。
*   **命令行启动器**: 在 `/usr/bin/` 中创建一个符号链接，让你可以直接从终端运行应用程序。
*   **桌面和图标集成**: 智能查找并安装图标文件到 `/usr/share/icons/`，并修改 `.desktop` 文件以确保其在应用菜单中正确显示。
*   **依赖项管理**: 默认添加了运行AppImage所需的核心依赖（如`libfuse2`），你也可以轻松自定义。
*   **高度可定制**: 提供了丰富的命令行选项，可以覆盖自动检测到的任何包信息（名称、版本、维护者等）。
*   **健壮的打包流程**: 使用 `fakeroot` 和 `dpkg-deb` 来构建包，确保权限和所有权正确。

## ⚙️ 先决条件

在运行此脚本之前，请确保你的系统（Debian, Ubuntu, Linux Mint等）已安装以下工具：

*   Python 3
*   `dpkg-deb` (来自 `dpkg-dev` 包)
*   `fakeroot`
*   `libfuse2` 或 `fuse` (大多数AppImage均需要)

你可以通过以下命令一次性安装所有依赖：

```bash
sudo apt update
sudo apt install python3 dpkg-dev fakeroot libfuse2
```

## 🚀 如何使用

1.  **保存脚本**: 将下面的Python代码保存为一个文件，例如 `appimage2deb.py`。

2.  **授予执行权限**: 在终端中，使用以下命令使脚本可执行：

    ```bash
    chmod +x appimage2deb.py
    ```

3.  **运行脚本**:

    *   **基本用法** (自动检测所有信息):

        ```bash
        ./appimage2deb.py /path/to/YourApplication.AppImage
        ```
        这将在当前目录下生成一个 `.deb` 文件。

    *   **高级用法** (自定义包信息):

        ```bash
        ./appimage2deb.py YourApp-1.2.3.AppImage -n my-cool-app -v 1.2.3 -m "Your Name <you@email.com>" -o ./packages
        ```
        这个命令会：
        *   将包名设置为 `my-cool-app`。
        *   将版本号设置为 `1.2.3`。
        *   设置维护者信息。
        *   将生成的 `.deb` 文件输出到 `./packages` 目录。

## 📋 命令行选项

| 短选项 | 长选项          | 描述                                                           | 默认值                                              |
| :----- | :-------------- | :------------------------------------------------------------- | :-------------------------------------------------- |
| (无)   | `appimage_path` | **[必需]** AppImage文件的路径。                                | (无)                                                |
| `-o`   | `--output-dir`  | 生成的`.deb`文件的输出目录。                                  | 当前目录                                            |
| `-n`   | `--name`        | 覆盖自动检测的软件包名称。                                     | 从 `.desktop` 文件名派生                            |
| `-v`   | `--version`     | 覆盖自动检测的版本号。                                         | 从 `X-AppImage-Version` 提取                        |
| `-m`   | `--maintainer`  | 包的维护者信息。                                               | 当前用户                                            |
| `-w`   | `--homepage`    | 应用程序的主页URL。                                            | `https://example.com`                               |
| `-d`   | `--description` | 短描述 (在 `apt` 列表中显示)。                                 | 从 `.desktop` 文件的 `Name` 字段提取              |
| `-l`   | `--long-desc`   | 详细描述。                                                     | "This package provides..."                        |
| `-s`   | `--section`     | 软件包分类 (如 `graphics`, `network`, `utils`)。               | `misc`                                              |
| `-p`   | `--priority`    | 软件包优先级 (如 `optional`, `required`)。                     | `optional`                                          |
| `-D`   | `--depends`     | 自定义软件包依赖关系。                                         | `libc6 (>= 2.31), libfuse2 \| fuse`                 |


## 🔬 工作原理

脚本通过以下步骤将AppImage转换为一个规范的Debian包：

1.  **提取**: 使用 `--appimage-extract` 命令将AppImage解压到一个临时目录。
2.  **解析**: 在解压后的目录中查找 `.desktop` 文件和图标文件，以获取元数据。
3.  **创建结构**: 在一个临时暂存区创建标准的Debian包目录结构（如 `DEBIAN/`, `usr/bin/`, `usr/lib/`, `usr/share/applications/` 等）。
4.  **放置文件**:
    *   将 **完整的AppImage文件** 复制到 `/usr/lib/<包名>/`。
    *   在 `/usr/bin/` 中创建一个指向上述AppImage的 **符号链接**，作为命令启动器。
    *   将找到的 **图标文件** 复制到 `/usr/share/icons/hicolor/scalable/apps/`。
    *   **修改并保存 `.desktop` 文件** 到 `/usr/share/applications/`，确保 `Exec=` 和 `Icon=` 字段指向新的启动器和图标。
5.  **生成控制文件**: 根据提取和用户指定的参数，创建 `DEBIAN/control` 文件，它包含了包的所有元数据。同时也会创建一个 `DEBIAN/postinst` 脚本，用于在安装后更新桌面和图标缓存。
6.  **打包**:调用 `fakeroot dpkg-deb --build` 命令，将暂存区打包成一个最终的 `.deb` 文件。
7.  **清理**: 删除所有临时文件和目录。
