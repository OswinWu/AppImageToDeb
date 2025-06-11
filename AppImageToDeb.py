#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
import re
import datetime
from pathlib import Path

def run_command(command, **kwargs):
    """辅助函数，用于运行命令并处理错误"""
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Creates a robust Debian package from an AppImage file.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('appimage_path', help='Path to the AppImage file')
    parser.add_argument('-o', '--output-dir', default=os.getcwd(), help='Output directory for the deb file (default: current directory)')
    parser.add_argument('-n', '--name', help='Override package name (default: derived from desktop file)')
    parser.add_argument('-v', '--version', help='Override version (default: from X-AppImage-Version)')
    parser.add_argument('-m', '--maintainer', default=f"{os.environ.get('USER', 'unknown')} <no-reply@example.com>", help='Maintainer info (default: current user)')
    parser.add_argument('-w', '--homepage', default='https://example.com', help='Homepage URL (default: example.com)')
    parser.add_argument('-d', '--description', help='Short description (default: from desktop file)')
    parser.add_argument('-l', '--long-desc', default='This package provides the application as a standard system install.', help='Long description')
    parser.add_argument('-s', '--section', default='misc', help='Package section (default: misc)')
    parser.add_argument('-p', '--priority', default='optional', help='Package priority (default: optional)')
    parser.add_argument('-D', '--depends', default='libc6 (>= 2.31), libfuse2 | fuse', help='Package dependencies (default: "libc6 (>= 2.31), libfuse2 | fuse")')

    return parser.parse_args()

def extract_appimage(appimage_path, build_dir):
    """提取AppImage的内容到临时目录"""
    print(f"Extracting AppImage: {appimage_path}")
    temp_appimage = Path(build_dir) / "app.AppImage"
    shutil.copy2(appimage_path, temp_appimage)
    temp_appimage.chmod(0o755)

    run_command([str(temp_appimage), '--appimage-extract'], cwd=build_dir)

    extract_dir = Path(build_dir) / "squashfs-root"
    if not extract_dir.is_dir():
        print("Error: AppImage extraction failed, squashfs-root directory not found")
        sys.exit(1)
    return extract_dir

def find_desktop_file(extract_dir):
    """查找.desktop文件"""
    desktop_files = list(extract_dir.glob("**/*.desktop"))
    if not desktop_files:
        print("Error: No desktop file found in the AppImage")
        sys.exit(1)
    return desktop_files[0]

def parse_desktop_file(desktop_path):
    """从.desktop文件内容中提取信息"""
    content = desktop_path.read_text(encoding='utf-8')
    info = {
        'Name': re.search(r'^Name=(.*)', content, re.MULTILINE),
        'Icon': re.search(r'^Icon=(.*)', content, re.MULTILINE),
        'Version': re.search(r'^X-AppImage-Version=(.*)', content, re.MULTILINE),
        'GenericName': re.search(r'^GenericName=(.*)', content, re.MULTILINE),
        'Comment': re.search(r'^Comment=(.*)', content, re.MULTILINE),
    }

    if not info['Version']:
        info['Version'] = re.search(r'^Version=(.*)', content, re.MULTILINE)

    for key, match in info.items():
        info[key] = match.group(1).strip() if match else None

    return info

def find_icon_file(extract_dir, icon_name):
    """在提取目录中查找最佳的图标文件"""
    if not icon_name:
        return None

    # 优先SVG
    for icon_file in extract_dir.glob(f"**/{icon_name}.svg"):
        return icon_file
    
    # 其次是PNG (寻找分辨率最高的)
    png_files = sorted(
        extract_dir.glob(f"**/{icon_name}.png"),
        key=lambda p: int(re.search(r'(\d+)', str(p.parent.name)).group(1)) if re.search(r'(\d+)', str(p.parent.name)) else 0,
        reverse=True
    )
    if png_files:
        return png_files[0]

    # 最后尝试任何匹配的图标
    all_icons = list(extract_dir.glob(f"**/{icon_name}.*"))
    if all_icons:
        return all_icons[0]

    return None

def create_deb_package(args, extract_dir):
    """创建Debian包"""
    # 1. 查找并解析元数据
    desktop_path = find_desktop_file(extract_dir)
    print(f"Using desktop file: {desktop_path}")
    desktop_info = parse_desktop_file(desktop_path)

    # 2. 决定包名、版本等
    # 使用正则表达式从 .desktop 文件名中提取更干净的包名
    pkg_name_base = re.sub(r'\.(desktop)$', '', desktop_path.name, flags=re.IGNORECASE)
    pkg_name = args.name or pkg_name_base.lower().replace(" ", "-")
    version = args.version or desktop_info.get('Version') or datetime.datetime.now().strftime("%Y%m%d")
    description = args.description or desktop_info.get('Name') or "Packaged from AppImage"
    icon_name = desktop_info.get('Icon')

    print(f"Package Name: {pkg_name}, Version: {version}")

    # 3. 创建打包暂存区
    arch_deb = run_command(['dpkg', '--print-architecture']).stdout.strip()
    stage_name = f"{pkg_name}_{version}_{arch_deb}"
    stage_dir = Path(args.output_dir) / stage_name
    if stage_dir.exists():
        shutil.rmtree(stage_dir)

    debian_dir = stage_dir / "DEBIAN"
    usr_lib_dir = stage_dir / "usr/lib" / pkg_name
    usr_bin_dir = stage_dir / "usr/bin"
    apps_dir = stage_dir / "usr/share/applications"
    icons_dir = stage_dir / "usr/share/icons/hicolor/scalable/apps"

    for d in [debian_dir, usr_lib_dir, usr_bin_dir, apps_dir, icons_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 4. 填充文件
    appimage_target_path = usr_lib_dir / f"{pkg_name}.AppImage"
    shutil.copy2(args.appimage_path, appimage_target_path)
    appimage_target_path.chmod(0o755)

    symlink_path = usr_bin_dir / pkg_name
    symlink_target = f"../lib/{pkg_name}/{pkg_name}.AppImage"
    os.symlink(symlink_target, symlink_path)

    icon_file = find_icon_file(extract_dir, icon_name)
    if icon_file:
        print(f"Found icon: {icon_file}")
        shutil.copy2(icon_file, icons_dir / f"{pkg_name}{icon_file.suffix}")
        icon_field_value = pkg_name
    else:
        print(f"Warning: Icon '{icon_name}' not found.")
        icon_field_value = icon_name

    desktop_content = desktop_path.read_text(encoding='utf-8')
    desktop_content = re.sub(r'^Exec=.*', f'Exec={pkg_name} %U', desktop_content, flags=re.MULTILINE)
    desktop_content = re.sub(r'^Icon=.*', f'Icon={icon_field_value}', desktop_content, flags=re.MULTILINE)
    (apps_dir / f"{pkg_name}.desktop").write_text(desktop_content, encoding='utf-8')

    # 5. 创建DEBIAN控制文件
    installed_size = run_command(['du', '-ks', stage_dir]).stdout.split()[0]
    # 注意多行Description的格式，长描述前需要有空格
    control_content = f"""Package: {pkg_name}
Version: {version}
Architecture: {arch_deb}
Maintainer: {args.maintainer}
Installed-Size: {installed_size}
Depends: {args.depends}
Section: {args.section}
Priority: {args.priority}
Homepage: {args.homepage}
Description: {description}
 {args.long_desc}
"""
    #  --- 关键修复在这里 ---
    (debian_dir / "control").write_text(control_content.strip() + '\n', encoding='utf-8')

    # 创建 postinst 脚本
    postinst_content = """#!/bin/sh
set -e
echo "Updating desktop database and icon caches..."
update-desktop-database -q || true
gtk-update-icon-cache -q /usr/share/icons/hicolor || true
exit 0
"""
    postinst_path = debian_dir / "postinst"
    postinst_path.write_text(postinst_content, encoding='utf-8')
    postinst_path.chmod(0o755)
    
    # 6. 打包
    deb_file = f"{stage_name}.deb"
    final_deb_path = Path(args.output_dir) / deb_file
    print(f"\nBuilding Debian package: {final_deb_path}")
    run_command(['fakeroot', 'dpkg-deb', '--build', str(stage_dir), str(final_deb_path)])
    
    print(f"\nSuccessfully built {final_deb_path}")
    print(f"To install: sudo apt install ./{final_deb_path.name}")
    
    # 清理
    shutil.rmtree(stage_dir)


def main():
    args = parse_args()
    appimage_path = Path(args.appimage_path)

    if not appimage_path.is_file():
        print(f"Error: AppImage file not found: {appimage_path}")
        sys.exit(1)

    appimage_path.chmod(appimage_path.stat().st_mode | 0o111)
    Path(args.output_dir).mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as build_dir:
        extract_dir = extract_appimage(appimage_path, build_dir)
        create_deb_package(args, extract_dir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
