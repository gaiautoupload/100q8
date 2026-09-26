"""Export the RACE research ledgers into one GitHub Pages JSON file."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from datetime import date
from transfer_adjustments import apply as apply_transfers
from champion_export import export as export_champion

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def broker_names(path):
    try:
        import pandas as pd
        f=pd.read_excel(path)
        return {str(x['證券商代號']).strip():str(x['證券商名稱']).strip() for _,x in f.iterrows()}
    except Exception:return {}
def clean_name(value,fallback):
    value=str(value or '').strip()
    return fallback if not value or '�' in value else value
def main():
    p=argparse.ArgumentParser();p.add_argument('--lab',type=Path,default=Path('../race-five-stock-lab'));p.add_argument('--broker-file',type=Path,default=Path(r'D:\stock_TradingBot\證券商基本資料.xls'));p.add_argument('--output',type=Path,default=Path('data/dashboard.json'));a=p.parse_args()
    stage4=a.lab/'reports-9359-stage4'/'79fab4ec7d58';stage3=a.lab/'reports-9359-stage3-strict'/'3a17a3dd4f70'
    names=broker_names(a.broker_file);config=load(stage4/'config.json');asof=config['end']
    companies={}
    listing=Path(config['listing_companies'])
    if listing.exists():
        for x in load(listing):companies[str(x.get('SecuritiesCompanyCode','')).strip()]=str(x.get('CompanyAbbreviation','')).strip()
    desc={'P19':('訊號日資金加分','RACE共同新建倉直接評分；9359訊號日買超採階梯加分','主對照'), 'P35':('後續資金確認','共同新建倉後第1–5日等待9359首次正淨買，次日最早成交','主要挑戰者'),'P40':('第一日快速確認','只接受訊號後第1日9359轉買；樣本不足','研究標籤')}
    summaries={}
    for code,base in [('P19',stage4),('P35',stage4),('P40',stage4)]:
        s=load(base/code/'summary.json');annual=rows(base/code/'annual.csv');s['annualized_pct']=float(annual[-1]['return_pct']);summaries[code]=s
    win={'P19':46.1538461538,'P35':56.25,'P40':100.0};closed={'P19':39,'P35':16,'P40':6}
    strategies=[{'code':c,'name':desc[c][0],'rule':desc[c][1],'status':desc[c][2],'return_pct':summaries[c]['return_pct'],'annualized_pct':summaries[c]['annualized_pct'],'max_drawdown_pct':summaries[c]['max_drawdown_pct'],'win_rate_pct':win[c],'closed_cycles':closed[c],'ending_equity':summaries[c]['ending_equity']} for c in ('P19','P35','P40')]
    watch=rows(a.lab/'paper_etf_dual'/'model_watchlist.csv');event_rows={x['id']:x for x in rows(stage3/'events.csv')};stocks={};strategy_holdings={'P19':[],'P35':[],'P40':[]};holding_age={}
    for plan,base in (('P19',stage3),('P35',stage3),('P40',stage4)):
        history=rows(base/plan/'holdings.csv');plan_asof=max(x['date'] for x in history)
        for current in (x for x in history if x['date']==plan_asof):
            episode=[x for x in history if x['stock']==current['stock'] and x['entry_index']==current['entry_index']]
            entry_date=min(x['date'] for x in episode);sessions=len({x['date'] for x in episode})
            shares=float(current['shares']);cost=float(current['cost']);market=float(current['market_value'])
            holding_age[(plan,current['stock'])]={'entry_date':entry_date,'holding_sessions':sessions,'holding_calendar_days':(date.fromisoformat(plan_asof)-date.fromisoformat(entry_date)).days+1,'score':float(current['score'] or 0),'cost':cost,'avg_cost':cost/shares if shares else 0,'mark':float(current['mark']),'market_value':market,'unrealized_pnl':market-cost,'unrealized_return_pct':100*(market/cost-1) if cost else 0}
    for w in watch:
        code=w['stock'];event=next((e for e in event_rows.values() if e['stock']==code and e['date']==w['source_signal']),None) or {}
        item=stocks.setdefault(code,{'stock':code,'name':clean_name(companies.get(code),code),'plans':[],'score':float(w['score'] or 0),'market_value':0.,'signal_date':w['source_signal'],'broker_9359_amount':float(event.get('broker_9359_amount') or 0),'listing_age':int(float(event['listing_age'])) if event.get('listing_age') else None,'brokers':[]})
        item['plans'].append(w['plan']);item['market_value']+=float(w['historical_model_shares'])*float(w['mark']);item['score']=max(item['score'],float(w['score'] or 0))
        if event.get('brokers'):
            item['brokers']=[{'code':b,'name':clean_name(names.get(b),'分點 '+b),'weight':v} for b,v in json.loads(event['brokers']).items()]
        age=holding_age.get((w['plan'],code),{})
        strategy_holdings[w['plan']].append({'plan':w['plan'],'stock':code,'name':clean_name(companies.get(code),code),'score':float(w['score'] or 0),'shares':float(w['historical_model_shares']),'mark':age.get('mark',float(w['mark'])),'cost':age.get('cost',0),'avg_cost':age.get('avg_cost',0),'market_value':age.get('market_value',float(w['historical_model_shares'])*float(w['mark'])),'unrealized_pnl':age.get('unrealized_pnl',0),'unrealized_return_pct':age.get('unrealized_return_pct',0),'signal_date':w['source_signal'],'entry_date':age.get('entry_date'),'holding_sessions':age.get('holding_sessions',0),'holding_calendar_days':age.get('holding_calendar_days',0),'broker_9359_amount':float(event.get('broker_9359_amount') or 0),'listing_age':int(float(event['listing_age'])) if event.get('listing_age') else None,'brokers':item['brokers']})
    p40_account=load(stage4/'P40'/'paper_account.json')
    for code,position in p40_account['positions'].items():
        event=position['event'];age=holding_age[('P40',code)];name=clean_name(event.get('name') or companies.get(code),code)
        broker_list=[{'code':b,'name':clean_name(names.get(b),'分點 '+b),'weight':v} for b,v in event.get('brokers',{}).items()]
        item=stocks.setdefault(code,{'stock':code,'name':name,'plans':[],'score':float(age.get('score',0)),'market_value':0.,'signal_date':event['date'],'broker_9359_amount':float(event.get('broker_9359_amount') or 0),'listing_age':int(float(event['listing_age'])) if event.get('listing_age') is not None else None,'brokers':broker_list})
        item['plans'].append('P40');item['market_value']+=age['market_value'];item['score']=max(item['score'],float(age.get('score',0)))
        strategy_holdings['P40'].append({'plan':'P40','stock':code,'name':name,'score':float(age.get('score',0)),'shares':float(position['shares']),'mark':age['mark'],'cost':age['cost'],'avg_cost':age['avg_cost'],'market_value':age['market_value'],'unrealized_pnl':age['unrealized_pnl'],'unrealized_return_pct':age['unrealized_return_pct'],'signal_date':event['date'],'entry_date':age['entry_date'],'holding_sessions':age['holding_sessions'],'holding_calendar_days':age['holding_calendar_days'],'broker_9359_amount':float(event.get('broker_9359_amount') or 0),'listing_age':int(float(event['listing_age'])) if event.get('listing_age') is not None else None,'brokers':broker_list})
    ranks=rows(stage4/'rank_history.csv');latest=max(x['effective_date'] for x in ranks if x['effective_date']);brokers=[]
    for x in ranks:
        if x['effective_date']!=latest:continue
        code=x['broker'];brokers.append({'rank':int(x['rank']),'code':code,'name':clean_name(names.get(code),'分點 '+code),'weight':float(x['weight']),'quality':float(x['quality']),'win_rate':float(x['win_rate_shrunk']),'mature_labels':int(x['mature_labels']),'return_score':float(x['score'])})
    brokers.sort(key=lambda x:x['rank'])
    for plan in strategy_holdings:strategy_holdings[plan].sort(key=lambda x:(-x['score'],x['stock']))
    p19={x['stock']:x for x in strategy_holdings['P19']};p35={x['stock']:x for x in strategy_holdings['P35']}
    common=[]
    for code in sorted(set(p19)&set(p35)):
        common.append({'stock':code,'name':p19[code]['name'],'P19':p19[code],'P35':p35[code]})
    portfolio_overview={}
    for plan,base in (('P19',stage3),('P35',stage3),('P40',stage4)):
        account=load(base/plan/'paper_account.json');holdings=strategy_holdings[plan];position_cost=sum(x['cost'] for x in holdings);market_value=sum(x['market_value'] for x in holdings);receivables=sum(float(x[1]) for x in account.get('receivables',[]));equity=float(account['cash'])+receivables+market_value
        portfolio_overview[plan]={'equity':equity,'total_return_pct':100*(equity/300000-1),'cash':float(account['cash']),'receivables':receivables,'position_cost':position_cost,'market_value':market_value,'unrealized_pnl':market_value-position_cost,'unrealized_return_pct':100*(market_value/position_cost-1) if position_cost else 0,'positions':len(holdings)}
    data={'as_of':asof,'rank_effective_date':latest,'paper_status':'等待截止日後的新訊號','strategies':strategies,'stocks':sorted(stocks.values(),key=lambda x:(-x['score'],x['stock'])),'strategy_holdings':strategy_holdings,'common_holdings':common,'portfolio_overview':portfolio_overview,'brokers':brokers,
      'featured_brokers':[{'code':'9359','name':'華南永昌-中正','roster_status':'資金確認分點・不等同前60名','role':'共同新建倉出現時，作為外部資金確認；不是共同建倉發起者，也不以其單獨賣超機械出場。','p19_basis':'訊號日金額階梯','p35_basis':'後1–5日首次轉買','caveat':'分點彙總'}],
      'formula':{'stock_score':[{'name':'淨買強度','points':30,'detail':'當日與近3日加權淨買／成交額百分位'},{'name':'買方共識','points':20,'detail':'淨買分點權重占買賣雙方權重'},{'name':'持續買進','points':20,'detail':'近5日加權淨買為正天數比例'},{'name':'原建倉者支持','points':20,'detail':'原始分點現存推估庫存／高點'},{'name':'賣壓控制','points':10,'detail':'近3日加權賣出金額反向比例'}], 'money_tiers':[{'amount':'100萬','points':5},{'amount':'300萬','points':10},{'amount':'600萬','points':15},{'amount':'1,000萬','points':20},{'amount':'2,000萬','points':25}]},
      'limitations':['所有交易均為紙上研究，並非實際成交或報酬保證。','分點能力只使用當時已成熟事件；至少10件、5檔股票才入選。','推估庫存來自券商分點交易流，不是官方公布的單一投資人持股。','公司行動、股利及歷史轉板事件尚未全量核實。','T+1日均價、滑價及成交容量皆為保守代理，不能保證實際成交。']}
    apply_transfers(data, config['raw_root'])
    data['champion']=export_champion(a.lab)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'output':str(a.output),'as_of':asof,'strategies':len(strategies),'stocks':len(data['stocks']),'brokers':len(brokers)},ensure_ascii=False))
if __name__=='__main__':main()
