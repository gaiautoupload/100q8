import csv,json,math
from datetime import date

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def export(lab):
    pointer=json.loads((lab/'champion_latest.json').read_text(encoding='utf-8'))
    from pathlib import Path
    folder=Path(pointer['path'])
    result=read_account(folder,pointer)
    result['paper']=read_account(folder/'paper',pointer)
    return result

def read_account(folder,pointer):
    daily=rows(folder/'daily.csv');history=rows(folder/'holdings.csv');asof=pointer['as_of']
    config=json.loads((folder/'config.json').read_text(encoding='utf-8'))
    events={e['id']:e for e in json.loads((folder/'events.json').read_text(encoding='utf-8'))}
    names={e['stock']:e.get('name',e['stock']) for e in events.values()}
    holdings=[]
    for r in history:
        if r['date']!=asof:continue
        episode=[x for x in history if x['stock']==r['stock'] and x['entry_index']==r['entry_index']]
        cost=float(r['cost']);market=float(r['market_value']);shares=float(r['shares']);entry=min(x['date'] for x in episode)
        holdings.append(dict(stock=r['stock'],name=names.get(r['stock'],r['stock']),shares=shares,cost=cost,avg_cost=cost/shares,mark=float(r['mark']),market_value=market,pnl=market-cost,return_pct=100*(market/cost-1),entry_date=entry,holding_sessions=len(episode),calendar_days=(date.fromisoformat(asof)-date.fromisoformat(entry)).days+1,score=float(r['score'] or 0),stale_sessions=int(r['stale_sessions'])))
    orders=rows(folder/'orders.csv');fills=rows(folder/'fills.csv');attempts=rows(folder/'attempts.csv')
    for r in orders:
        r['name']=names.get(r['stock'],r['stock']);r['fills']=[x for x in fills if x['order_id']==r['id']];r['attempts']=[x for x in attempts if x['order_id']==r['id']]
    account=daily[-1] if daily else dict(equity=config['capital'],cash=config['capital'],receivable=0,market_value=0,positions=0)
    pending=json.loads((folder/'pending.json').read_text(encoding='utf-8'))
    # Size estimates use only the latest known quote. Tomorrow's fill is unknown.
    import gzip
    with gzip.open(__import__('pathlib').Path(config['source_cache'])/(asof+'.json.gz'),'rt',encoding='utf-8') as f:quotes=json.load(f)['quotes']
    remaining_cash=float(account['cash'])
    for order in sorted(pending,key=lambda x:(x['side']!='sell',x['stock'])):
        held=next((h for h in holdings if h['stock']==order['stock']),None)
        q=quotes.get(order['stock']);order['reference_price']=q[0] if q else None
        if order['side']=='sell':order['estimated_shares']=min(held['shares'],order['quantity'] or held['shares']) if held else 0
        elif q:
            price=q[0]*(1+config['slippage']);capacity=min(order['signal_turnover'],q[3])*config['participation']
            budget=min(order['budget'],remaining_cash);unit=config['lot']
            qty=max(0,math.floor(min(capacity/price,max(0,budget-config['minimum_fee'])/(price*(1+config['commission'])))/unit)*unit)
            order['estimated_shares']=qty;order['estimated_cash']=qty*price+max(config['minimum_fee'],qty*price*config['commission']) if qty else 0
            remaining_cash-=order['estimated_cash']
        else:order['estimated_shares']=None
    return dict(as_of=asof,start=config['start'],capital=config['capital'],version=pointer['version'],summary=json.loads((folder/'summary.json').read_text(encoding='utf-8')),account=account,holdings=holdings,orders=orders[::-1],pending=pending,dates=sorted({x['signal_date'] for x in orders},reverse=True),names=names,settlements=rows(folder/'settlements.csv'))
