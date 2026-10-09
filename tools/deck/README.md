# tools/deck: A2UI payload to .pptx

Turns an A2UI payload (or a typed scene list) into a .pptx that opens in Google Slides and PowerPoint. `deck_build.py` is the reference converter
(python-pptx, Roboto metrics from Pillow); `payload_to_deck.py` maps atoms to scenes; `recipes_more.py` holds the atom recipes.

The same converter runs on the MCP server as a JavaScript port (in the private worker), with a small hand-written PPTX writer instead of python-pptx.

## How it is checked

- The file is read back and linted: overlap, bounds, contrast (4.5:1), an 18 pt floor, alt text. A deck that cannot fit is refused with the slide and field.
- The output is byte-reproducible: stored (uncompressed) zip, fixed timestamps, no random ids. Tests in Python and JavaScript build twice and compare bytes.
- `verify_slides.py` uploads to Google Drive, lets Google convert it, reads the result back and renders each slide.
- `validate_ooxml.py` checks every slide, layout, master and theme part against the ECMA-376 transitional schemas (legal OOXML, not layout).

## Known limits

- **Two writers, one scene list.** Python and the JavaScript port both read the same typed scene list. What is duplicated is the text fitting and layout code,
  not the format. A parity suite (135 recipe cases, compared shape for shape) catches a recipe or layout that lands in one writer only. It does not catch
  both writers sharing a wrong font metric, because their shapes would still match each other. Treat that as a residual risk, not something to redesign now.
- **The hand-written writer is a frozen subset.** The JavaScript writer is small on purpose (text, shapes, tables, pictures, notes, hyperlinks, one QR
  vector shape). If it starts to need charts, animations or themes, use python-pptx's model rather than growing it. The read-back is the contract.
- **Which consumers have seen it.** Google Slides (checked each release). A schema check of 31 generated decks (all 10 layouts, both targets, 214+ slides)
  found no illegal parts. LibreOffice Impress rendered a sample of those decks to PDF with the layouts intact and no overflow; Roboto was installed
  there, so that run did not exercise the wider-fallback-font margin. Desktop PowerPoint has not been used to open these files, so keep saying
  "checked in Google Slides" until it has.
- **Atoms with no recipe** are reported as unsupported on the MCP tools. The Python converter can draw one as a picture (`atom_image.py`); the Worker cannot.
- **Timing.** Compile alone, measured with the JavaScript port in Node on a small laptop: about 30 ms for a 3-slide deck and 170 to 440 ms for 15 slides. Not timed on the
  deployed Worker. A request-to-checked-deck figure (the model choosing atoms, a person checking) is a different number; do not quote one for the other.
