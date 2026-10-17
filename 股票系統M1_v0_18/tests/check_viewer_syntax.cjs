const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..');const html=fs.readFileSync(path.join(root,'價格結構重播.html'),'utf8');
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];new vm.Script(script);
fs.writeFileSync(path.join(root,'output','JavaScript語法檢查.json'),JSON.stringify({status:'PASS',check:'Node vm.Script compile',browser_interaction:'NOT_TESTED_BY_THIS_CHECK'},null,2));
console.log('JavaScript syntax PASS. No browser interaction claimed.');
