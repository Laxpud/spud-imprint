# Spud Imprint

Spud Imprint is a batch photo imprint and watermark tool.

[中文 README](README.md)

This repository is being modernized from an earlier Pillow script into a reusable Python package. The current priority is to stabilize the image processing core and CLI before building a modern cross-platform GUI on top of the same core.

## Current Status

- Python image processing core based on Pillow.
- Batch processing CLI as the first stable interface.
- Future GUI planned with Tauri and React/TypeScript.
- Future interactive preview planned with Konva.js or a similar Canvas tool.

## Development Environment

`uv` is recommended for managing the Python virtual environment and dependencies:

```powershell
uv venv
uv pip install -e .
```

The standard `venv` workflow also works:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## Run Batch Processing

```powershell
python -m spud_imprint batch `
  --input .\input `
  --output .\output `
  --config .\examples\config.example.toml
```

The command scans the input directory for common image formats, renders the configured imprint, and writes exported images into the output directory.

Local source photos and generated outputs are intentionally ignored by Git. Put local real-photo test inputs here:

```text
local/real-tests/input/
```

Put corresponding outputs here:

```text
local/real-tests/output/
```

The `local/` directory is local-only and ignored by Git.

## Run Tests

```powershell
python -m unittest discover -s tests
```

The current tests use generated small images and temporary directories. Real photos are usually large and may contain private or copyrighted metadata, so they are not committed by default.

For local manual testing with real photos, run:

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\examples\config.example.toml
```

## Development Rules

See [docs/development.md](docs/development.md) for repository conventions.

Key rules:

- The default README is Chinese, with `README.en.md` maintained alongside it.
- AI assistants should write new or edited Python comments and docstrings in Chinese; this is not a strict requirement for human contributors.
- Identifiers, CLI commands, logs, terminal output, and config keys remain English.
- Test assets should be small, sanitized, and reproducible fixtures; real working photos should not be committed directly.

## Roadmap

1. Preserve the original scripts under `legacy/`.
2. Stabilize the core modules under `src/spud_imprint`.
3. Improve the configuration-driven CLI.
4. Expand tests around metadata, layout, export, and end-to-end batch processing.
5. Start the desktop GUI after the core logic is stable.
