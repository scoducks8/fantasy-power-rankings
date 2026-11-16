// Scoreboard for the weekly power rankings game.
// Paste into a new Apps Script project (script.google.com), then
// Deploy > New deployment > Web app, Execute as: Me, Who has access: Anyone.
// It creates its own Google Sheet ("Power rankings game scores") on first use.

const TAB = 'scores';

function sheet_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('SHEET_ID');
  if (id) return SpreadsheetApp.openById(id).getSheetByName(TAB);
  const ss = SpreadsheetApp.create('Power rankings game scores');
  props.setProperty('SHEET_ID', ss.getId());
  const sh = ss.getSheets()[0];
  sh.setName(TAB);
  sh.appendRow(['time', 'week', 'name', 'score', 'shipped', 'seconds']);
  return sh;
}

function top_(week, n) {
  const rows = sheet_().getDataRange().getValues().slice(1)
    .filter(r => String(r[1]) === String(week))
    .sort((a, b) => b[3] - a[3]);
  const seen = {}, out = [];
  for (const r of rows) {
    const k = String(r[2]).toLowerCase();
    if (seen[k]) continue;          // best score per name
    seen[k] = true;
    out.push({ name: String(r[2]), score: Number(r[3]), shipped: Number(r[4]), secs: Number(r[5]) });
    if (out.length >= n) break;
  }
  return out;
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return json_({ top: top_(e.parameter.week || '', 10) });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(5000);
  try {
    const d = JSON.parse(e.postData.contents);
    const name = String(d.name || '').replace(/[^\w .'-]/g, '').trim().slice(0, 12);
    const score = Math.floor(Number(d.score));
    const week = Math.floor(Number(d.week));
    if (!name || !(score >= 0 && score <= 60000) || !(week >= 1 && week <= 18)) return json_({ ok: false });
    sheet_().appendRow([new Date(), week, name, score, Math.floor(Number(d.shipped)) || 0, Math.floor(Number(d.secs)) || 0]);
    return json_({ ok: true, top: top_(week, 10) });
  } finally {
    lock.releaseLock();
  }
}
