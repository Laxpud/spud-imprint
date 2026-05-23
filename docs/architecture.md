# Architecture

## Direction

Laxpud Imprint should evolve as a layered tool:

1. A Python core library for image loading, layout, EXIF metadata extraction, text
   rendering, and export.
2. A Python CLI for batch processing and automation.
3. A future Tauri desktop app with a React/TypeScript front end for a modern,
   cross-platform GUI.

The GUI should call the same core processing model used by the CLI. The preview
editor and final export should share one configuration schema so the rendered
output matches what the user saw in the preview.

## Technology Decisions

- Keep Python for the first core implementation because the existing code is
  Python and Pillow already handles the required image operations.
- Use a CLI before a GUI so batch behavior is testable and scriptable.
- Use Tauri + React/TypeScript for the future GUI when interactive previews are
  needed.
- Use Konva.js or a similar canvas library for direct manipulation in the preview
  editor.
- Consider a Rust rendering core later only if distribution size or runtime
  dependency concerns become important enough to justify the rewrite.

## Packaging Direction

The first packaged GUI can ship a Python CLI as a Tauri sidecar. End users should
not need to install Python manually. If package size becomes a hard constraint,
the rendering core can be migrated behind the same configuration schema.

