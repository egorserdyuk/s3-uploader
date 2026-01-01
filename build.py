#!/usr/bin/env python3
"""PyInstaller build script for S3 Uploader
Creates executables for Windows, macOS, and Linux with different architectures
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

# Supported platforms and architectures
SUPPORTED_PLATFORMS = {
    "windows": ["x86", "x64", "arm64"],
    "darwin": ["x64", "arm64"],  # macOS
    "linux": ["x86", "x64", "arm64", "armv7l"],
}

# Platform name mappings
PLATFORM_NAMES = {"windows": "win", "darwin": "macos", "linux": "linux"}

# Architecture mappings
ARCH_NAMES = {"x86": "32", "x64": "64", "arm64": "arm64", "armv7l": "armv7"}


class BuildConfig:
    """Build configuration"""

    def __init__(self, platform: str, arch: str, output_dir: str):
        self.platform = platform
        self.arch = arch
        self.output_dir = Path(output_dir)
        self.name = f"s3-uploader-{PLATFORM_NAMES[platform]}{ARCH_NAMES[arch]}"

        # Determine executable extension
        if platform == "windows":
            self.exe_name = f"{self.name}.exe"
        else:
            self.exe_name = self.name

        # Determine PyInstaller target architecture
        if platform == "windows" and arch == "x86":
            self.target_arch = "win32"
        elif platform == "windows" and arch == "x64":
            self.target_arch = "win64"
        else:
            self.target_arch = None  # Let PyInstaller auto-detect


def check_dependencies() -> None:
    """Check if required dependencies are installed"""
    try:
        import pyinstaller

        print(f"{Fore.GREEN}✓ PyInstaller is installed")
    except ImportError:
        print(f"{Fore.RED}✗ PyInstaller is not installed")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    try:
        import boto3

        print(f"{Fore.GREEN}✓ boto3 is installed")
    except ImportError:
        print(f"{Fore.RED}✗ boto3 is not installed")
        print("Install it with: pip install boto3")
        sys.exit(1)


def create_spec_file(config: BuildConfig) -> str:
    """Create PyInstaller spec file content"""
    # Determine hidden imports based on platform
    hidden_imports = [
        "boto3",
        "botocore",
        "colorama",
        "tqdm",
        "argparse",
        "json",
        "os",
        "sys",
        "time",
        "pathlib",
        "typing",
        "urllib.parse",
    ]

    # Add platform-specific imports
    if config.platform == "windows":
        hidden_imports.extend(["colorama.win32", "colorama.ansitowin32"])

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['s3_uploader.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('creds.json', '.'),
    ],
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{config.name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='{config.target_arch}' if '{config.target_arch}' else None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    return spec_content


def build_for_config(config: BuildConfig) -> bool:
    """Build executable for a specific configuration"""
    print(f"\n{Fore.CYAN}Building for {config.platform} {config.arch}...")

    # Create output directory
    build_dir = config.output_dir / config.platform / config.arch
    build_dir.mkdir(parents=True, exist_ok=True)

    # Create spec file
    spec_content = create_spec_file(config)
    spec_file = build_dir / f"{config.name}.spec"

    try:
        with open(spec_file, "w") as f:
            f.write(spec_content)

        # Run PyInstaller
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name",
            config.name,
            "--distpath",
            str(build_dir),
            "--workpath",
            str(build_dir / "build"),
            "--specpath",
            str(build_dir),
            "--add-data",
            "creds.json:.",
            "s3_uploader.py",
        ]

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ Build successful for {config.platform} {config.arch}")

            # Check if executable was created
            exe_path = build_dir / config.exe_name
            if exe_path.exists():
                size = exe_path.stat().st_size
                print(f"{Fore.CYAN}Executable size: {size / 1024 / 1024:.2f} MB")
                return True
            print(f"{Fore.RED}✗ Executable not found at {exe_path}")
            return False
        print(f"{Fore.RED}✗ Build failed for {config.platform} {config.arch}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

    except Exception as e:
        print(f"{Fore.RED}✗ Build error for {config.platform} {config.arch}: {e}")
        return False


def create_multi_platform_installer(
    configs: list[BuildConfig],
    output_dir: Path,
) -> None:
    """Create a multi-platform installer script"""
    installer_content = """#!/bin/bash
# S3 Uploader Multi-Platform Installer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM=""
ARCH=""

# Detect platform
case "$(uname -s)" in
    CYGWIN*|MINGW*|MSYS*)
        PLATFORM="windows"
        ;;
    Darwin)
        PLATFORM="darwin"
        ;;
    Linux)
        PLATFORM="linux"
        ;;
    *)
        echo "Unsupported platform: $(uname -s)"
        exit 1
        ;;
esac

# Detect architecture
case "$(uname -m)" in
    i386|i686)
        ARCH="x86"
        ;;
    x86_64|amd64)
        ARCH="x64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    armv7l)
        ARCH="armv7l"
        ;;
    *)
        echo "Unsupported architecture: $(uname -m)"
        exit 1
        ;;
esac

echo "Detected platform: $PLATFORM $ARCH"

# Find and run the appropriate executable
EXECUTABLE="$SCRIPT_DIR/$PLATFORM/$ARCH/s3-uploader-${PLATFORM:0:3}${ARCH:0:2}"

if [ "$PLATFORM" = "windows" ]; then
    EXECUTABLE="$EXECUTABLE.exe"
fi

if [ -f "$EXECUTABLE" ]; then
    echo "Running: $EXECUTABLE"
    exec "$EXECUTABLE" "$@"
else
    echo "Error: Executable not found at $EXECUTABLE"
    echo "Available platforms:"
    find "$SCRIPT_DIR" -name "s3-uploader-*" -type f | sort
    exit 1
fi
"""

    installer_file = output_dir / "install.sh"
    with open(installer_file, "w") as f:
        f.write(installer_content)

    # Make installer executable
    os.chmod(installer_file, 0o755)
    print(f"{Fore.GREEN}✓ Created multi-platform installer: {installer_file}")


def create_readme(output_dir: Path, configs: list[BuildConfig]) -> None:
    """Create README with build information"""
    readme_content = """# S3 Uploader Builds

This directory contains compiled executables for S3 Uploader.

## Available Builds

"""

    for config in configs:
        readme_content += f"- **{config.platform.title()} {config.arch}**: `{config.platform}/{config.arch}/{config.exe_name}`\n"

    readme_content += """

## Usage

### Direct Execution

Navigate to the appropriate platform/architecture directory and run the executable:

```bash
# Linux x64
./linux/x64/s3-uploader-linux64

# Windows x64
./windows/x64/s3-uploader-win64.exe

# macOS ARM64
./darwin/arm64/s3-uploader-macosarm64
```

### Multi-Platform Installer

Use the `install.sh` script for automatic platform detection:

```bash
./install.sh upload local_file.txt s3://my-bucket/files/
```

## Commands

See the main README for detailed command usage.

## Credentials

Before using the executable, create a `creds.json` file in the same directory with your S3 credentials:

```json
{
  "aws_access_key_id": "YOUR_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_SECRET_KEY",
  "region_name": "us-east-1",
  "endpoint_url": "https://your-s3-endpoint.com"
}
```

## Build Information

- Built with PyInstaller
- Single-file executable
- Includes all dependencies
- Platform-specific optimizations applied
"""

    readme_file = output_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)

    print(f"{Fore.GREEN}✓ Created README: {readme_file}")


def main():
    """Main build function"""
    parser = argparse.ArgumentParser(
        description="Build S3 Uploader for multiple platforms",
    )
    parser.add_argument(
        "--platform",
        choices=SUPPORTED_PLATFORMS.keys(),
        help="Target platform",
    )
    parser.add_argument(
        "--arch",
        choices=["x86", "x64", "arm64", "armv7l"],
        help="Target architecture",
    )
    parser.add_argument(
        "--output",
        default="dist",
        help="Output directory (default: dist)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Build for all supported platforms",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before building",
    )

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    # Determine configurations to build
    configs = []

    if args.all:
        # Build for all platforms and architectures
        for platform, archs in SUPPORTED_PLATFORMS.items():
            for arch in archs:
                configs.append(BuildConfig(platform, arch, args.output))
    elif args.platform and args.arch:
        # Build for specific platform and architecture
        if args.arch not in SUPPORTED_PLATFORMS.get(args.platform, []):
            print(
                f"{Fore.RED}Error: Architecture {args.arch} not supported for platform {args.platform}",
            )
            sys.exit(1)
        configs.append(BuildConfig(args.platform, args.arch, args.output))
    else:
        # Build for current platform and all supported architectures
        current_platform = platform.system().lower()
        if current_platform not in SUPPORTED_PLATFORMS:
            print(f"{Fore.RED}Error: Current platform {current_platform} not supported")
            sys.exit(1)

        current_arch = platform.machine().lower()
        if current_arch == "amd64":
            current_arch = "x64"
        elif current_arch == "i386":
            current_arch = "x86"

        if current_arch not in SUPPORTED_PLATFORMS[current_platform]:
            print(
                f"{Fore.RED}Error: Current architecture {current_arch} not supported for platform {current_platform}",
            )
            sys.exit(1)

        configs.append(BuildConfig(current_platform, current_arch, args.output))

    # Clean output directory if requested
    if args.clean:
        output_dir = Path(args.output)
        if output_dir.exists():
            print(f"{Fore.YELLOW}Cleaning output directory: {output_dir}")
            shutil.rmtree(output_dir)

    # Build configurations
    successful_builds = []
    failed_builds = []

    for config in configs:
        if build_for_config(config):
            successful_builds.append(config)
        else:
            failed_builds.append(config)

    # Create installer and documentation
    if successful_builds:
        output_dir = Path(args.output)
        create_multi_platform_installer(successful_builds, output_dir)
        create_readme(output_dir, successful_builds)

    # Print summary
    print(f"\n{Fore.CYAN}Build Summary:")
    print(f"Successful: {len(successful_builds)}")
    print(f"Failed: {len(failed_builds)}")

    if failed_builds:
        print("\nFailed builds:")
        for config in failed_builds:
            print(f"  - {config.platform} {config.arch}")
        sys.exit(1)

    print(f"\n{Fore.GREEN}All builds completed successfully!")
    print(f"Executables available in: {args.output}")


if __name__ == "__main__":
    # Import colorama for colored output
    try:
        from colorama import Fore, Style, init

        init()
    except ImportError:
        Fore = type("Fore", (), {"GREEN": "", "RED": "", "CYAN": "", "YELLOW": ""})()

    main()
