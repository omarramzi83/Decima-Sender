import os
import sys
import subprocess
import requests
from PIL import Image
from io import BytesIO

def install_requirements():
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def download_icon():
    print("Downloading icon...")
    # Using a direct PNG icon instead of SVG for simplicity
    icon_url = "https://img.icons8.com/fluency/96/mail.png"
    response = requests.get(icon_url)
    
    if response.status_code == 200:
        # Save the PNG directly as ICO
        with open("icon.ico", "wb") as f:
            f.write(response.content)
        print("Icon downloaded successfully")
    else:
        print("Failed to download icon")

def create_spec_file():
    print("Creating spec file...")
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates')],
    hiddenimports=['werkzeug.middleware.proxy_fix'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name='Decima-Sender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)"""
    
    with open("decima_sender.spec", "w") as f:
        f.write(spec_content)

def build_executable():
    print("Building executable...")
    subprocess.check_call(["pyinstaller", "decima_sender.spec", "--clean"])

def main():
    try:
        # Create directories if they don't exist
        os.makedirs("templates", exist_ok=True)
        os.makedirs("dist", exist_ok=True)
        os.makedirs("build", exist_ok=True)
        
        # Run the build steps
        install_requirements()
        download_icon()
        create_spec_file()
        build_executable()
        
        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist' folder")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
