import fs from 'fs';
import path from 'path';
import { JSDOM } from '/home/hatch/workspace/crossqa-pr104-delta/repo/node_modules/jsdom/lib/api.js';

const ROOT='/home/hatch/workspace/crossqa-pr104-delta/repo';
const EV='/home/hatch/workspace/crossqa-pr104-delta/output/evidence';
const dvd = JSON.parse(fs.readFileSync('/tmp/dvd-selectors.json','utf-8'));

function ev(doc, sel){
  try{
    const r = doc.evaluate(sel, doc, null, doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    const out=[];
    for(let i=0;i<r.snapshotLength;i++){const n=r.snapshotItem(i); out.push(n.nodeValue!==null?n.nodeValue:n.textContent.trim());}
    return out;
  }catch(e){ return 'XPATH-ERROR: '+e.message; }
}
const files = [];
for (const f of fs.readdirSync(ROOT+'/tests/fixtures/bravo').filter(x=>x.startsWith('dvd-synthetic-')).sort())
  files.push([f, fs.readFileSync(ROOT+'/tests/fixtures/bravo/'+f,'utf-8')]);
for (const f of fs.readdirSync(EV).filter(x=>x.startsWith('adv-')).sort())
  files.push([f, fs.readFileSync(EV+'/'+f,'utf-8')]);
for (const [name, content] of files){
  const doc = new JSDOM(content).window.document;
  console.log(`${name}: URLs=${JSON.stringify(ev(doc, dvd.URLs))} Title=${JSON.stringify(ev(doc, dvd.Title))} Code=${JSON.stringify(ev(doc, dvd.Code))}`);
}
