/**
 * A2UI Efficiency Playbook — Google Apps Script Web App
 * Recreates the atom_efficiency visual: 35× token comparison.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI · Token Efficiency · 2026')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
