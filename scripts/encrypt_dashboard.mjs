import {createCipheriv,createHash,randomBytes} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
const passwords=(process.env.Q8_PASSWORDS||'').split(';').filter(Boolean);
if(!passwords.length)throw new Error('Set Q8_PASSWORDS with semicolon-separated passwords');
const source=readFileSync('data/dashboard.json');
const envelopes=passwords.map(password=>{
  const key=createHash('sha256').update(password).digest();const iv=randomBytes(12);
  const cipher=createCipheriv('aes-256-gcm',key,iv);const encrypted=Buffer.concat([cipher.update(source),cipher.final(),cipher.getAuthTag()]);
  return {iv:iv.toString('base64'),data:encrypted.toString('base64')};
});
writeFileSync('data/dashboard.secure.json',JSON.stringify({version:1,algorithm:'AES-256-GCM',envelopes},null,2));
console.log(JSON.stringify({output:'data/dashboard.secure.json',envelopes:envelopes.length,plaintext_bytes:source.length}));
