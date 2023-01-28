# -*- mode: python -*-
import os, tld

block_cipher = None


a = Analysis(['accesser/__main__.py'],
             pathex=['./'],
             binaries=[],
             datas=[('accesser/config.toml', 'accesser'),
                    ('accesser/pac', 'accesser'),
                    (os.path.dirname(tld.__file__)+'/res/effective_tld_names.dat.txt', 'tld/res')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='accesser',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
