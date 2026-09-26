const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 for(const width of [360,390,768,1440]){
  const page=await browser.newPage({viewport:{width,height:844},isMobile:width<700,hasTouch:width<700});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto((process.env.Q8_TEST_URL||'http://127.0.0.1:8765/')+'#champion');
  await page.locator('#site-password').fill(process.env.Q8_PASSWORDS.split(';')[0]);await page.locator('#unlock-form button').click();
  await page.locator('#champion.active').waitFor();await page.locator('#champion-metrics b').first().waitFor();
  await page.locator('[data-champ="hold"]').click();await page.locator('#champ-hold:not([hidden])').waitFor();
  const holdings=await page.locator('#champ-holdings .stock-card').count();
  await page.locator('[data-champ="history"]').click();await page.locator('#champ-side').selectOption('sell');
  await page.locator('#champ-orders details').first().locator('summary').click();
  if(!await page.locator('#champ-orders details').first().getAttribute('open').then(x=>x!==null))throw Error('Expand failed');
  const count=await page.locator('#champ-count').innerText();
  await page.locator('#champ-date').selectOption({index:1});
  await page.locator('[data-champ="rules"]').click();
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
  if(errors.length||overflow)throw Error(JSON.stringify({width,errors,overflow}));
  await page.locator('[data-champ="action"]').click();
  if(width===390)await page.screenshot({path:'site-mobile-preview.png',fullPage:true});
  console.log(JSON.stringify({width,holdings,count,errors,overflow}));await page.close();
 }await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
