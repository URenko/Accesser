# -*- mode: python -*-

block_cipher = None


a = Analysis(['accesser.py'],
             pathex=['./'],
             binaries=[],
             datas=[('config.json.default', '.'),
                    ('template/pac', 'template'),
                    ('template/index.html', 'template'),
                    ('static/main.js', 'static'),
                    ('static/style.css', 'static'),
                    ('{{tld_path}}/res/effective_tld_names.dat.txt', 'tld/res')],
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
