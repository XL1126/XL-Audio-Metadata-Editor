# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['音频嵌入图片-豆包.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'os',
        'tempfile',
        'shutil',
        'base64',
        'mutagen',
        'mutagen.id3',
        'threading',
        'io',
        'PIL._tkinter_finder'  # 解决PIL与tkinter结合的特殊依赖
    ],
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
    name='XL音频元数据编辑工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩以减小文件体积
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示命令窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='XL.png'  # 使用同目录下的XL.png作为图标
)
    