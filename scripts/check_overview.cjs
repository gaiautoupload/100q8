const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 for(const scenario of ['normal','malformed-cache','storage-blocked','render-failure','download-failure']){
  const page=await browser.newPage({viewport:{width:390,height:844}});
  if(scenario==='malformed-cache')await page.addInitScript(()=>sessionStorage.setItem('100q8_payload','{bad'));
  if(scenario==='storage-blocked')await page.addInitScript(()=>{Storage.prototype.getItem=()=>{throw Error('blocked')};Storage.prototype.setItem=()=>{throw Error('quota')}});
  if(scenario==='download-failure')await page.route('**/data/dashboard.secure.json',r=>r.abort());
  const url=(process.env.Q8_TEST_URL||'http://127.0.0.1:8765/')+'#overview';await page.goto(url);
  if(scenario==='download-failure'){
   await page.locator('#lock-error').filter({hasText:'下載失敗'}).waitFor();
   if(!await page.locator('#reload-data').isVisible())throw Error('Missing recovery');
  }else{
   if(scenario==='render-failure')await page.evaluate(()=>document.getElementById('latest-overview').remove());
   await page.locator('#site-password').fill(process.env.Q8_PASSWORDS.split(';')[0]);await page.locator('#unlock-form button[type="submit"]').click();
   if(scenario==='render-failure'){
    await page.locator('#lock-error').filter({hasText:'解鎖成功'}).waitFor();
    if(!await page.locator('#lock-screen').isVisible())throw Error('Render failure left blank unlocked page');
   }else{
    await page.locator('body:not(.locked)').waitFor();
    if(await page.locator('.overview-stock-list>div').count()<1)throw Error('Overview stocks absent');
    if(!(await page.locator('#asof').innerText()).includes('最新策略'))throw Error('Overview still uses archived date label');
    if(!(await page.locator('#latest-overview').innerText()).includes('100,000'))throw Error('Capital missing');
    if(scenario==='normal')await page.screenshot({path:'site-mobile-preview.png',fullPage:true});
    await page.locator('#open-model').click();await page.locator('#champ-hold:not([hidden])').waitFor();
    if(await page.locator('#champ-account').inputValue()!=='model')throw Error('Wrong account');
    await page.locator('[data-view="overview"]').click();await page.locator('#open-new-account').click();
    if(await page.locator('#champ-account').inputValue()!=='paper')throw Error('Wrong new account');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Overflow');
   }
  }
  console.log('PASS '+scenario);await page.close();
 }await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
