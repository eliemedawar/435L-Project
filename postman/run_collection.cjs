// Execute the real Postman runtime and save only redacted evidence.
// Developed by: Marc Bteich.
const fs=require('fs');
const path=require('path');
const newman=require('../.local/tooling/node_modules/newman');
const root=path.resolve(__dirname,'..');
const [collectionFile, privateEnvironmentFile, outputName]=process.argv.slice(2);
if(!collectionFile || !privateEnvironmentFile || !outputName) throw Error('Expected collection, private environment, evidence name');
const privateValues=JSON.parse(fs.readFileSync(privateEnvironmentFile,'utf8'));
const secretValues=Object.entries(privateValues).filter(([key])=>/password|token|service_key/i.test(key)).map(([,v])=>v).filter(Boolean);
function redact(value,key=''){
  if(/password|token|authorization|service.?key/i.test(key)) return '[REDACTED]';
  if(Array.isArray(value)) return value.map(v=>redact(v));
  if(value && typeof value==='object') return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,redact(v,k)]));
  if(typeof value==='string'){
    for(const secret of secretValues) value=value.split(secret).join('[REDACTED]');
    return value.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,'[REDACTED JWT]');
  }
  return value;
}
const records=[];
const runtime=newman.run({collection:JSON.parse(fs.readFileSync(collectionFile,'utf8')),
  environment:{name:'Private local runtime',values:Object.entries(privateValues).map(([key,value])=>({key,value,enabled:true}))},
  reporters:[],timeoutRequest:15000,timeoutScript:10000},(error,summary)=>{
  if(error) throw error;
  const result={source:'Actual Newman/Postman Runtime execution; secrets redacted',
    collection:path.basename(collectionFile),executed_at:new Date().toISOString(),
    requests:summary.run.stats.requests,assertions:summary.run.stats.assertions,
    failures:summary.run.failures.map(f=>({name:f.error.name,message:redact(f.error.message),at:f.at,request:f.source?.name})),records};
  fs.mkdirSync(path.join(root,'report/evidence'),{recursive:true});
  fs.writeFileSync(path.join(root,'report/evidence',outputName+'.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({collection:result.collection,requests:result.requests,assertions:result.assertions,failures:result.failures},null,2));
  process.exitCode=result.failures.length?1:0;
});
runtime.on('request',(err,args)=>{
  let response=null,body=null;
  try{response=JSON.parse(args.response.stream.toString());}catch{response=args.response?.stream?.toString();}
  try{body=JSON.parse(args.request.body?.raw || 'null');}catch{body=args.request.body?.raw;}
  records.push({name:args.item.name,method:args.request.method,url:args.request.url.toString(),
    request:redact(body),status:args.response?.code,response:redact(response),error:err?redact(String(err)):null});
});
