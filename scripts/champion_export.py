import csv,json
from datetime import date

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def export(lab):
    pointer=json.loads((lab/'champion_latest.json').read_text(encoding='utf-8'))
    from pathlib import Path
    folder=Path(pointer['path']);daily=rows(folder/'daily.csv');history=rows(folder/'holdings.csv');asof=pointer['as_of']
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
    return dict(as_of=asof,version=pointer['version'],summary=json.loads((folder/'summary.json').read_text(encoding='utf-8')),account=daily[-1],holdings=holdings,orders=orders[::-1],pending=json.loads((folder/'pending.json').read_text(encoding='utf-8')),dates=sorted({x['signal_date'] for x in orders},reverse=True),names=names,settlements=rows(folder/'settlements.csv'))
