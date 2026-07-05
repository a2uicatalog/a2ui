/**
 * A2UI — Apps Script Web App Surface Pitch
 * Public web app demonstrating A2UI atoms rendered on the google-apps-script-web surface.
 *
 * Rendered server-side by apps_script_web.py (Python preview renderer).
 * In a live deployment, swap doGet() for one that calls renderAtoms(BLOCKS)
 * from atom.gs to get real Workspace data (Drive, Sheets, Gmail, Calendar).
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI — Apps Script Web App Surface')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
