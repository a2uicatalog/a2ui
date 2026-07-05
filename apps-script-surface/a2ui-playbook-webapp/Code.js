/**
 * A2UI Playbook Catalogue — public web app.
 * Lists and previews every MeetStudio playbook, rendered via the GDM→HTML engine.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI Playbook Catalogue')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
