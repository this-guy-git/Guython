import PyInstaller.__main__

PyInstaller.__main__.run([
    'run.py',
    '--onefile',
    '--icon=icon.ico',
    '--add-data=guython;guython'
])