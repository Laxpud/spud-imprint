# Laxpud Imprint

Batch photo imprint and watermark tooling.

This repository is being modernized from an earlier Pillow script into a reusable
Python package with a CLI first. The long-term plan is to keep the image
processing core independent so it can be reused by a future modern cross-platform
desktop GUI.

## Current Status

- Python image processing core based on Pillow
- Batch processing CLI as the first stable interface
- GUI planned later with Tauri, React/TypeScript, and an interactive canvas

## Install For Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## Run

```powershell
python -m laxpud_imprint batch `
  --input .\input `
  --output .\output `
  --config .\examples\config.example.toml
```

The command scans the input directory for common image formats, renders the
configured imprint, and writes exported images into the output directory.

Local source photos and generated outputs are intentionally ignored by Git. Keep
your own working photos in an ignored folder such as `input/`.

## Development Roadmap

1. Preserve the original scripts as legacy reference.
2. Move the current v0.4 implementation into `src/laxpud_imprint`.
3. Add a configuration-driven CLI.
4. Add tests around metadata formatting, layout calculations, and export behavior.
5. Add the desktop GUI after the core package is stable.
