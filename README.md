# PolarDisk

A free offline Windows desktop utility from **PolarLabs-OSS**.

![PolarDisk icon](PolarDisk.png)

## Features

# PolarDisk v1.0

Applicazione desktop di analisi dello spazio su disco in sola lettura. Mostra i 1000 file più grandi, raggruppa per sottocartella e permette l'esportazione CSV dell'intera scansione. Ignora symlink e junction. Non elimina né modifica i file.

## Install and run from source

Requires Python 3 with Tkinter. Install dependencies via `pip install -r requirements.txt`, then run:

```powershell
python polardisk.py
```

## Windows release

Download the Windows x64 release ZIP, extract the **entire archive** and run `PolarDisk-PolarWhite-v5.exe`. Do not move the EXE away from the `_internal` directory. The x64 build was tested on Windows 11 ARM64 under emulation.

## Linux

The Linux ARM64 binary was compiled in Ubuntu WSL but its interactive desktop UI was not fully tested. Other Linux architectures require a native rebuild.

## Security and privacy

File processing happens locally. The executable is not digitally signed, so your device or organization's application-control policy may restrict launching it. Do not disable security protections to run it.

## License

MIT License — see [LICENSE](LICENSE).

PolarLabs / Space Services SRLS · https://www.polarlabs.it/
