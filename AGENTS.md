# AI Agent Instructions

This file defines repository-specific instructions for AI coding agents.

## Project Direction

- Keep the image processing core in Python for now.
- Keep CLI behavior stable before starting the desktop GUI.
- Future GUI direction: Tauri + React/TypeScript, with interactive preview handled by Konva.js or a similar Canvas library.
- Do not rewrite the rendering core in Rust unless package size or distribution constraints become a concrete priority.

## Language Rules

- Use English for code identifiers, module names, CLI commands, terminal output, log messages, exception messages, and config keys.
- When an AI agent adds or edits Python comments or docstrings, write those comments/docstrings in Chinese.
- The Chinese comment/docstring rule is for AI agents only. Do not present it as a hard requirement for human contributors.
- Keep user-facing default documentation in Chinese. Maintain `README.en.md` when changing `README.md`.

## Python Style

- Follow PEP 8 for formatting and PEP 257 for docstrings.
- Add Chinese comments and docstrings generously enough that a reader with little coding experience can quickly understand what each meaningful block of code is doing and why it exists.
- Prefer short block-level comments before important steps, branches, loops, data transformations, image geometry calculations, coordinate calculations, format conversions, configuration handling, and edge-case handling.
- Avoid noisy line-by-line comments that only repeat obvious assignments or function calls; comments should explain purpose, data flow, assumptions, or the reason behind a choice.
- Public classes, public functions, and complex private methods should have concise Chinese docstrings that explain their role, key inputs, outputs, and any important side effects.

## Testing Rules

- Run the default test command before committing:

```powershell
python -m unittest discover -s tests
```

- Prefer generated images and temporary directories for fast tests.
- Real photo assets should not be committed by default.
- Local real-photo manual test inputs belong under `local/real-tests/input/`.
- Local real-photo manual test outputs belong under `local/real-tests/output/`.
- If fixture images are needed, place small, sanitized, redistributable files under `tests/fixtures/`.

## Git And Assets

- Do not create versioned script files such as `v0.5.py`; use Git commits and tags.
- Keep original legacy scripts under `legacy/`.
- Do not commit generated outputs, working photos, caches, or virtual environments.
- Keep `local/` ignored; it is reserved for local-only real-photo tests.
- Keep the root directory focused on project metadata and source folders.

## Dependency Management

- Prefer `uv` for local Python environment setup:

```powershell
uv venv
uv pip install -e .
```

- `uv` is a development tool preference, not an end-user runtime dependency.
