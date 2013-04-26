# -*- mode: python -*-
a = Analysis(['pg.py'],
             hiddenimports=[],
             hookspath=None)
             
a.datas += [
                  ('dep/pg.png', 'dep/pg.png', 'DATA'),
                  ('dep/viewer.html', 'dep/viewer.html', 'DATA'),
                  ('requests/cacert.pem', 'requests/cacert.pem', 'DATA'),
             ]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'PhotoGrabber.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='dep\\pg.ico')
app = BUNDLE(exe,
             name=os.path.join('dist', 'PhotoGrabber.exe.app'))
