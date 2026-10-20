// Render documented DOT sources to standalone SVG. Developed by: Marc Bteich.
const fs=require('fs');
const path=require('path');
const {instance}=require('../.local/tooling/node_modules/@viz-js/viz');
(async()=>{
  const viz=await instance();
  for(const name of ['architecture','database']){
    const target=path.join(__dirname,'diagrams',name);
    fs.writeFileSync(target+'.svg',viz.renderString(fs.readFileSync(target+'.dot','utf8'),{format:'svg',engine:'dot'}));
  }
})();
