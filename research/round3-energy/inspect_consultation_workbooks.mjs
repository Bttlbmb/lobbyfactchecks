import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const root = new URL('./', import.meta.url).pathname;
const queue = JSON.parse(await fs.readFile(`${root}coverage-bmwe-dataset-download-queue-results.json`, 'utf8'));
const out = [];
for (const item of queue.filter(x => x.local_file.endsWith('.xlsx'))) {
  const file = await FileBlob.load(item.local_file);
  const workbook = await SpreadsheetFile.importXlsx(file);
  const overview = await workbook.inspect({kind:'workbook,sheet,table', maxChars:6000, tableMaxRows:3, tableMaxCols:8, tableMaxCellChars:80});
  const sheets = [];
  const sheetNames = overview.ndjson.split('\n').filter(Boolean).map(s=>JSON.parse(s)).filter(x=>x.kind==='sheet').map(x=>x.name);
  for (const name of sheetNames) {
    const sheet = workbook.worksheets.getItem(name);
    const range = sheet.getUsedRange(true);
    const rows = range.values;
    sheets.push({name:sheet.name, range:range.address, rows:rows.length, columns:Math.max(0,...rows.map(r=>r.length)), first_rows:rows.slice(0,4).map(r=>r.slice(0,12))});
    if (['Datensatz','Complete','Dataset','Structure','Variables'].includes(sheet.name)) {
      await fs.writeFile(`${root}sources/bmwe-datasets/${item.id}-${sheet.name}.json`, JSON.stringify(rows,null,2)+'\n');
    }
  }
  out.push({id:item.id, source:item.local_file, dataset:item.dataset_title, overview:overview.ndjson, sheets, depth:'metadata_only; workbook structure and source-row identities, not all answer contents reviewed'});
}
await fs.writeFile(`${root}coverage-bmwe-workbook-structure.json`,JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify(out));
