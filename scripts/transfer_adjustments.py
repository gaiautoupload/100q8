"""Explicit post-snapshot transfer settlement; does not claim a full replay."""
import csv
import hashlib
from pathlib import Path


def apply(data, raw_root):
    path = Path(raw_root) / 'quotes' / 'EMdes010.20260921-C.csv'
    with path.open(encoding='cp950', errors='strict', newline='') as f:
        records = list(csv.reader(f))
    matches = [r for r in records if len(r)>11 and r[0]=='BODY' and r[1].strip()=='7856']
    if len(matches)!=1:
        raise ValueError('Expected one official 7856 quote')
    price=float(matches[0][11].replace(',', '').strip())
    if price!=4550:
        raise ValueError('Unexpected last emerging price; review source')
    settlements=[]
    for plan, holdings in data['strategy_holdings'].items():
        holding=next((x for x in holdings if x['stock']=='7856'),None)
        if holding is None:
            continue
        gross=holding['shares']*price
        fee=max(20,gross*.001425); tax=gross*.003
        proceeds=gross-fee-tax; pnl=proceeds-holding['cost']
        row=dict(plan=plan,stock='7856',name='漢測',price_date='2026-09-21',transfer_date='2026-09-22',
                 shares=holding['shares'],price=price,gross=gross,fee=fee,tax=tax,net_proceeds=proceeds,
                 cost=holding['cost'],realized_pnl=pnl,return_pct=100*pnl/holding['cost'],
                 source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        settlements.append(row);holdings.remove(holding)
        account=data['portfolio_overview'][plan]
        account['receivables']+=proceeds
        account['market_value']-=holding['market_value'];account['position_cost']-=holding['cost']
        account['equity']+=proceeds-holding['market_value'];account['positions']=len(holdings)
        account['total_return_pct']=100*(account['equity']/300000-1)
        account['unrealized_pnl']=account['market_value']-account['position_cost']
        account['unrealized_return_pct']=100*account['unrealized_pnl']/account['position_cost'] if account['position_cost'] else 0
    data['stocks']=[x for x in data['stocks'] if x['stock']!='7856']
    data['common_holdings']=[x for x in data['common_holdings'] if x['stock']!='7856']
    data['transfer_settlements']=settlements
    data['settlement_note']='漢測已依9/21興櫃最後成交價4,550元補充結算、扣除費稅；其餘估值及策略績效仍截至9/18。補充結算款暫列待收款，尚未重播後續交割與換股。'
