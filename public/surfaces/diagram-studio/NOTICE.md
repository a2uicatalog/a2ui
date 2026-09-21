# Diagram Studio view: third-party notices

- **Mermaid** (https://github.com/mermaid-js/mermaid) is inlined in `view.html`. MIT License.
- **D2** (https://github.com/terrastruct/d2) and its JavaScript wrapper **@d2lang/d2** are shipped, WASM embedded, as
  `d2.bundle.mjs.gz` (gzip of the ES module). Mozilla Public License 2.0; the source is available from the upstream
  repositories above. This directory carries the unmodified upstream build.
- **draw.io** (https://github.com/jgraph/drawio), Apache License 2.0, and the mxGraph it embeds: the read-only viewer is shipped as
  `drawio-viewer.min.js.gz` (gzip of `viewer-static.min.js`). One change was made: its final start-up call, which fetches MathJax from
  viewer.diagrams.net and scans the page for diagrams, is replaced by a hook (`onDrawioViewerLoad`), so the page starts the viewer
  itself and nothing is requested from diagrams.net. Otherwise unmodified.
- **draw.io**, full editor: `drawio-editor/` is a self-hosted, minimal-asset copy of the same upstream editor (unmodified files,
  ~23 MB, a trimmed subset of the ~83 MB vendored tree; see `DRAWIO_EDITOR_FILES` in `build_view.py` for the exact list and why each
  entry is needed). "Edit in draw.io" opens it as a new top-level tab, loading the diagram via draw.io's own URL-fragment
  convention (`#R<base64>`); nothing is requested from diagrams.net.
