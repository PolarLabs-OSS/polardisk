Set-Location $PSScriptRoot
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name PolarDisk --icon PolarDisk.ico --add-data 'PolarDisk.ico;.' --add-data 'PolarDisk.png;.' polardisk.py
