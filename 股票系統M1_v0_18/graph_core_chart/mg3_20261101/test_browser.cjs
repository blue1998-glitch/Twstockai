'use strict';
// Reuse the original Chromium interaction/precision suite unchanged. Only the
// new artifact filename and additive 0.2 acceptance checks are injected.
const fs=require('fs'),path=require('path'),Module=require('module');
const original=path.resolve(__dirname,'../test_browser.cjs');
let source=fs.readFileSync(original,'utf8');
if(!source.includes('M1_v019_graph_recognition_v01.html'))throw Error('Original browser contract changed');
source=source.replace('M1_v019_graph_recognition_v01.html','M1_v019_graph_recognition_v02.html');
const marker='  await context.close();';
if(source.split(marker).length!==2)throw Error('Original browser injection boundary changed');
source=source.replace(marker,fs.readFileSync(path.join(__dirname,'browser_cases.js'),'utf8')+'\n'+marker);
const runner=new Module(original,module);runner.filename=original;runner.paths=Module._nodeModulePaths(path.dirname(original));runner._compile(source,original);
