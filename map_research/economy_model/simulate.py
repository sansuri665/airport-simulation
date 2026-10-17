#!/usr/bin/env python3
"""Railway real macro v0.2: 8x5 regional series + 2 national series, Python 3.10+.

This is a NEW standalone synthetic game engine, not a rerun of the Airport engine.
No weather, CPI, exchange rates, commercial assets, or company accounts are simulated.
All random streams are deterministic by (master seed, component, region), independent
of horizon and iteration order. Each year uses only previously known states and that
period's innovations. Reading a cached 60-year scenario must not reveal future data
to in-game agents: use public_snapshot(rows, current_year_index).
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGIONAL_METRICS = [
 'energy_real_index','wage_real_index','materials_real_index',
 'passenger_demand_index','freight_demand_index'
]
NATIONAL_METRICS = ['real_rate_pct','valuation_index']
CORE_METRICS = REGIONAL_METRICS + NATIONAL_METRICS

INDEX_METRICS = [m for m in CORE_METRICS if m != 'real_rate_pct']
META = {
 'energy_real_index':('实际电力价格','基期=100'),
 'wage_real_index':('实际工资','基期=100'),
 'materials_real_index':('实际材料工业品价格','基期=100'),
 'real_rate_pct':('实际融资基准利率','年化百分比；不是指数'),
 'passenger_demand_index':('客运需求','基期=100'),
 'freight_demand_index':('货运需求','基期=100'),
 'valuation_index':('行业PE参考指数','基期=100；PE倍数比'),
 'pe_multiple':('正常化盈利PE参照','倍；不是股价或总回报')
}

def load_config(path: str | Path = ROOT/'config.json') -> dict[str,Any]:
    cfg=json.loads(Path(path).read_text(encoding='utf-8'))
    validate_config(cfg)
    return cfg

def validate_config(cfg: dict[str,Any]) -> None:
    regions=cfg['regions']
    if len(regions)!=8 or len({r['id'] for r in regions})!=8:
        raise ValueError('Exactly eight unique region IDs are required.')
    ids={r['id'] for r in regions}
    if cfg['index_base']<=0:
        raise ValueError('Index base must be positive.')
    for r in regions:
        if not set(r['neighbors'])<=ids or r['id'] in r['neighbors']:
            raise ValueError(f"Invalid region calibration: {r['id']}")
    T=cfg['transition_matrix']
    if len(T)!=len(cfg['regimes']):
        raise ValueError('Wrong number of transition rows.')
    for row in T:
        if len(row)!=len(T) or any(x<0 for x in row) or abs(sum(row)-1)>1e-10:
            raise ValueError('Regime transition probabilities must be nonnegative and sum to one.')
    p=cfg['parameters']
    if p['national_pe_base']<=0:
        raise ValueError('National base PE must be positive.')
    if p['rate_floor_pct']>=p['rate_cap_pct'] or p['pe_floor']<=0 or p['pe_floor']>=p['pe_cap']:
        raise ValueError('Invalid numerical safety bounds.')
    if p.get('wage_labor_market_enabled'):
        for key in ('wage_slack_memory','wage_demand_loss_memory','wage_increase_adjustment','wage_decrease_adjustment','wage_level_correction'):
            if not isinstance(p.get(key),(int,float)) or not math.isfinite(p[key]) or not 0<p[key]<1:
                raise ValueError('Invalid wage adjustment parameter: '+key)
        for key in ('wage_demand_loss_beta','wage_weak_trend_reference','wage_weak_trend_beta','wage_activity_pressure_beta','wage_contraction_pressure_beta','wage_slowdown_pressure','wage_credit_pressure','wage_duration_pressure','wage_duration_limit','wage_pressure_level_years'):
            if not isinstance(p.get(key),(int,float)) or not math.isfinite(p[key]) or p[key]<0:
                raise ValueError('Invalid wage pressure parameter: '+key)
    paths=cfg.get('regional_development_paths')
    if paths is not None:
        if set(paths)!=ids:
            raise ValueError('Regional paths must cover exactly the configured regions.')
        for path in paths.values():
            if len(path)!=61:
                raise ValueError('Regional paths must contain the base year and 60 annual states.')
            for row in path:
                if not isinstance(row.get('name'),str) or any(not isinstance(row.get(key),(int,float)) or not math.isfinite(row[key]) for key in ('passenger','freight','wage','activity','energy','materials')):
                    raise ValueError('Invalid regional development state.')

def stream(seed: int, key: str) -> random.Random:
    digest=hashlib.sha256(f'rail-real-v02|{seed}|{key}'.encode()).digest()
    return random.Random(int.from_bytes(digest[:16],'big'))

def config_hash(cfg: dict[str,Any]) -> str:
    return hashlib.sha256(json.dumps(cfg,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def draw_regime(rng: random.Random, row: list[float]) -> int:
    u=rng.random(); acc=0.0
    for i,p in enumerate(row):
        acc+=p
        if u<acc:
            return i
    return len(row)-1

def clip(x:float,lo:float,hi:float)->tuple[float,int]:
    return max(lo,min(hi,x)),int(x<lo or x>hi)

def safe_exp(x:float)->float:
    if not math.isfinite(x) or abs(x)>650:
        raise FloatingPointError('Unstable log level. Review calibration; no silent index clipping.')
    return math.exp(x)

def simulate(cfg: dict[str,Any] | None=None, *, years:int=60, seed:int=20261014,
             start_year:int | None=None, shocks:dict[int,dict[str,Any]] | None=None)->dict[str,Any]:
    """Return annual region rows plus latent common factors and an event ledger.

    Optional diagnostic shock dictionary, e.g. {20: {'rate_pp': 2.0}}. Price
    shocks are temporary log deviations; passenger/freight shocks shift their
    accumulated demand trend once (a permanent level loss unless later offset).
    'regions' may restrict a shock to a subset; an absent list targets all eight.
    These overrides are stress tests, not part of the default sample.
    """
    cfg=copy.deepcopy(cfg if cfg is not None else load_config())
    validate_config(cfg)
    if isinstance(years,bool) or not isinstance(years,int) or not 0<=years<=500:
        raise ValueError('years must be an integer in [0,500].')
    if cfg.get('regional_development_paths') and years>60:
        raise ValueError('Regional game paths support at most 60 years.')
    if not isinstance(seed,int) or isinstance(seed,bool):
        raise ValueError('seed must be an integer.')
    start_year=cfg['base_year'] if start_year is None else start_year
    if not isinstance(start_year,int):
        raise ValueError('start_year must be an integer.')
    shocks=shocks or {}
    regions=sorted(cfg['regions'],key=lambda r:r['id'])
    reg={r['id']:r for r in regions}; p=cfg['parameters']; base=cfg['index_base']
    allowed={'energy_log','wage_log','materials_log','rate_pp','passenger_log','freight_log','valuation_log','regions','regime_index'}
    for t,shock in shocks.items():
        if not isinstance(t,int) or t<=0 or not set(shock)<=allowed:
            raise ValueError('Invalid stress-test key/year.')
        if not set(shock.get('regions',reg))<=set(reg):
            raise ValueError('Unknown shock region.')
        if 'regions' in shock and ({'rate_pp','valuation_log','regime_index'} & set(shock)):
            raise ValueError('National rate/PE shocks cannot be region-scoped.')
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) for k,v in shock.items() if k!='regions'):
            raise ValueError('Shock values must be finite numbers.')
        if 'regime_index' in shock and (isinstance(shock['regime_index'],bool) or not isinstance(shock['regime_index'],int) or not 0<=shock['regime_index']<len(cfg['regimes'])):
            raise ValueError('Invalid annual regime override.')
    rng=stream(seed,'national'); rr={r['id']:stream(seed,'region:'+r['id']) for r in regions}
    national=dict(cycle=0.,cycle_lag=0.,credit=0.,industry=0.,trade=0.,sentiment=0.,productivity=0.,
                  energy_log=0.,energy_secular=0.,materials_log=0.,materials_secular=0.,rate=p['national_real_rate_base_pct'],logpe=math.log(p['national_pe_base']),valuation_index=base,rate_bound_hit=0,pe_bound_hit=0,regime=0)
    state={r['id']:dict(cycle=0.,industry=0.,pstructure=0.,fstructure=0.,ptrend=0.,ftrend=0.,
          wage_log=0.,wage_growth=r['wage_initial_trend'],energy_log=0.,materials_log=0.,
          labor_slack=0.,labor_demand_loss=0.,weak_years=0,last_passenger_cycle_log=0.,last_freight_cycle_log=0.,
          wage_potential_log=0.,wage_potential_growth=r['wage_initial_trend']) for r in regions}
    rows=[]; factors=[]; events=[]
    def emit(t:int,r:dict[str,Any],s:dict[str,float],vals:dict[str,float],gp:float,gf:float,
             pcy:float=0.,fcy:float=0.)->None:
        rows.append(dict(year_index=t,calendar_year=start_year+t,region_id=r['id'],region_name=r['name'],
            **vals,pe_multiple=safe_exp(national['logpe']),regime=cfg['regimes'][national['regime']],
            regime_name=cfg['regime_names_zh'][national['regime']],national_cycle=national['cycle'],
            regional_cycle=s['cycle'],regional_industry_cycle=s['industry'],
            passenger_trend_growth_pct=gp*100,freight_trend_growth_pct=gf*100,
            passenger_structural_state_pp=s['pstructure']*100,freight_structural_state_pp=s['fstructure']*100,
            passenger_trend_log=s['ptrend'],freight_trend_log=s['ftrend'],passenger_cycle_log=pcy,freight_cycle_log=fcy,
            rate_safety_bound_hit=national['rate_bound_hit'],pe_safety_bound_hit=national['pe_bound_hit']))
    def emit_factor(t:int)->None:
        factors.append(dict(year_index=t,calendar_year=start_year+t,**national,
                            regime_name=cfg['regime_names_zh'][national['regime']]))
    # Base row consumes no random draws and is identical across all seeds.
    for r in regions:
        s=state[r['id']]
        vals={m:base for m in INDEX_METRICS}; vals['real_rate_pct']=national['rate']
        emit(0,r,s,vals,r['passenger_initial_trend'],r['freight_initial_trend'])
    emit_factor(0)
    for t in range(1,years+1):
        prev=copy.deepcopy(national); old=copy.deepcopy(state)
        shock=shocks.get(t,{})
        next_regime=draw_regime(rng,cfg['transition_matrix'][prev['regime']])
        if 'regime_index' in shock:
            next_regime=shock['regime_index']
        # Always draw the same number of innovations, even when an event is absent.
        z=[rng.gauss(0,1) for _ in range(11)]; u_event,u_sign,u_size=rng.random(),rng.random(),rng.random()
        supply_event=0.
        if u_event<p['energy_event_probability']:
            sign=1 if u_sign<p['energy_event_positive_probability'] else -1
            supply_event=sign*(p['energy_event_size_min']+u_size*(p['energy_event_size_max']-p['energy_event_size_min']))
            events.append(dict(year_index=t,calendar_year=start_year+t,event_type='energy_supply',region='all',
                               magnitude=supply_event,description='电力供给偏紧' if sign>0 else '电力供给宽松'))
        if next_regime!=prev['regime']:
            events.append(dict(year_index=t,calendar_year=start_year+t,event_type='regime_change',region='all',
                magnitude=0.,description=cfg['regime_names_zh'][prev['regime']]+' → '+cfg['regime_names_zh'][next_regime]))
        rho=p['cycle_radius']; a=2*rho*math.cos(2*math.pi/p['cycle_period_years'])
        raw=a*prev['cycle']-rho*rho*prev['cycle_lag']+cfg['regime_business_impulse'][next_regime]+p['cycle_noise']*z[0]
        national['cycle']=p['cycle_soft_scale']*math.tanh(raw/p['cycle_soft_scale'])
        national['cycle_lag']=prev['cycle']; national['regime']=next_regime
        c=national['cycle']
        national['credit']=p['credit_memory']*prev['credit']+(1-p['credit_memory'])*cfg['regime_credit_target'][next_regime]+p['credit_noise']*z[1]
        national['industry']=p['industrial_memory']*prev['industry']+p['industrial_cycle_beta']*c+p['industrial_noise']*z[2]
        national['trade']=p['trade_memory']*prev['trade']+p['trade_cycle_beta']*c+p['trade_noise']*z[3]
        national['sentiment']=p['sentiment_memory']*prev['sentiment']+p['sentiment_cycle_beta']*c+p['sentiment_credit_beta']*national['credit']+p['sentiment_noise']*z[4]
        national['productivity']=p['productivity_memory']*prev['productivity']+p['productivity_noise']*z[5]
        national['energy_secular']=prev['energy_secular']+p['energy_secular_noise']*z[6]
        national['energy_log']=p['energy_memory']*prev['energy_log']+p['energy_cycle_beta']*c+p['energy_noise']*z[7]+supply_event
        national['materials_secular']=prev['materials_secular']+p['materials_secular_noise']*z[8]
        national['materials_log']=p['materials_memory']*prev['materials_log']+p['materials_industry_beta']*national['industry']+p['materials_cycle_beta']*c+p['materials_supply_beta']*supply_event+p['materials_noise']*z[9]
        rt=p['national_real_rate_base_pct']+p['national_rate_cycle_pp']*c+p['national_rate_credit_pp']*national['credit']+p['national_rate_productivity_pp']*national['productivity']+p['national_rate_noise_pp']*z[10]
        shock=shocks.get(t,{})
        national['rate'],national['rate_bound_hit']=clip(
            p['national_rate_memory']*prev['rate']+(1-p['national_rate_memory'])*rt+float(shock.get('rate_pp',0.)),
            p['rate_floor_pct'],p['rate_cap_pct'])
        # One national capital market. No regional base PE, regional spreads or local valuation noise.
        # The expectation proxy uses only *current* observed cycle, industry/trade, sentiment and credit.
        common_growth_signal=p['pe_growth_driver_pp']*(0.55*national['industry']+0.45*national['trade'])
        pe_target=(math.log(p['national_pe_base'])
            + p['pe_rate_sensitivity_per_pp']*(national['rate']-p['national_real_rate_base_pct'])
            + p['pe_growth_sensitivity_per_pp']*common_growth_signal
            + p['pe_credit_sensitivity']*national['credit']
            + p['pe_sentiment_sensitivity']*national['sentiment']
            + p['pe_regional_cycle_sensitivity']*c
            + float(shock.get('valuation_log',0.)))
        raw_pe=safe_exp(p['pe_memory']*prev['logpe']+(1-p['pe_memory'])*pe_target)
        pe,national['pe_bound_hit']=clip(raw_pe,p['pe_floor'],p['pe_cap'])
        national['logpe']=math.log(pe)
        national['valuation_index']=base*pe/p['national_pe_base']
        for r in regions:
            rid=r['id']; o=old[rid]; s=state[rid]; rz=[rr[rid].gauss(0,1) for _ in range(12)]
            neighbors=sorted(r['neighbors'])
            avg=lambda key:math.fsum(old[n][key] for n in neighbors)/len(neighbors) if neighbors else o[key]
            active=rid in shock.get('regions',reg)
            x=lambda key:float(shock.get(key,0.)) if active else 0.
            local=cfg['regional_development_paths'][rid][t] if cfg.get('regional_development_paths') else None
            s['cycle']=p['regional_cycle_memory']*o['cycle']+p['regional_cycle_spillover']*avg('cycle')+p['regional_cycle_common']*c+p['regional_cycle_noise']*rz[0]
            if local:
                s['cycle']+=.12*local['activity']
            s['industry']=p['regional_industry_memory']*o['industry']+p['regional_industry_common']*national['industry']+p['regional_industry_cycle']*s['cycle']+p['regional_industry_noise']*rz[1]
            mix=p['structure_innovation_common_share']
            s['pstructure']=p['structure_memory']*o['pstructure']+p['structure_spillover']*avg('pstructure')+p['passenger_structure_noise']*rz[2]
            s['fstructure']=p['structure_memory']*o['fstructure']+p['structure_spillover']*avg('fstructure')+p['freight_structure_noise']*(mix*rz[2]+math.sqrt(1-mix*mix)*rz[3])
            gp=p['passenger_terminal_trend']+(r['passenger_initial_trend']-p['passenger_terminal_trend'])*math.exp(-t/p['maturation_years'])+p['passenger_structure_beta']*s['pstructure']+p['passenger_productivity_beta']*national['productivity']
            gf=p['freight_terminal_trend']+(r['freight_initial_trend']-p['freight_terminal_trend'])*math.exp(-t/p['maturation_years'])+p['freight_structure_beta']*s['fstructure']+p['freight_productivity_beta']*national['productivity']
            if local:
                gp=local['passenger']+p['passenger_structure_beta']*s['pstructure']+p['passenger_productivity_beta']*national['productivity']
                gf=local['freight']+p['freight_structure_beta']*s['fstructure']+p['freight_productivity_beta']*national['productivity']
            s['ptrend']=o['ptrend']+gp+x('passenger_log'); s['ftrend']=o['ftrend']+gf+x('freight_log')
            pc=r['passenger_cycle_beta']*(p['passenger_common_cycle_log']*c+p['passenger_regional_cycle_log']*s['cycle'])+r['tourism_exposure']*p['passenger_tourism_log']*national['sentiment']+p['passenger_noise_log']*rz[4]
            fc=r['freight_cycle_beta']*(p['freight_common_cycle_log']*c+p['freight_regional_cycle_log']*s['cycle']+p['freight_industry_log']*s['industry'])+r['trade_exposure']*p['freight_trade_log']*national['trade']+p['freight_noise_log']*rz[5]
            wg=p['wage_terminal_trend']+(r['wage_initial_trend']-p['wage_terminal_trend'])*math.exp(-t/p['wage_maturation_years'])+p['wage_structure_beta']*(s['pstructure']+s['fstructure'])+p['wage_productivity_beta']*national['productivity']+p['wage_cycle_beta']*o['cycle']
            if local:
                wg=local['wage']+p['wage_structure_beta']*(s['pstructure']+s['fstructure'])+p['wage_productivity_beta']*national['productivity']+p['wage_cycle_beta']*o['cycle']
            if p.get('wage_labor_market_enabled'):
                # Realized volume weakness and lasting demand losses feed a
                # persistent labor-market state. Wages react to LAST year's
                # state, so a short downturn first slows raises; sustained
                # pressure can cut real wages. Recovery raises wages gradually.
                demand_shock=0.6*x('passenger_log')+0.4*x('freight_log')
                s['labor_demand_loss']=max(0.,p['wage_demand_loss_memory']*o['labor_demand_loss']-demand_shock)
                realized_growth=(0.6*(gp+x('passenger_log')+pc-o['last_passenger_cycle_log'])
                                 +0.4*(gf+x('freight_log')+fc-o['last_freight_cycle_log']))
                s['weak_years']=min(p['wage_duration_limit'],o['weak_years']+1) if realized_growth<0 or s['cycle']<-.65 else max(0,o['weak_years']-1)
                underlying_growth=0.6*gp+0.4*gf
                target_slack=(p['wage_demand_loss_beta']*s['labor_demand_loss']
                              +p['wage_weak_trend_beta']*max(0.,p['wage_weak_trend_reference']-underlying_growth)
                              +p['wage_activity_pressure_beta']*max(0.,-s['cycle'])
                              +p['wage_contraction_pressure_beta']*max(0.,-realized_growth)
                              +p['wage_duration_pressure']*s['weak_years']
                              +(p['wage_slowdown_pressure'] if next_regime==2 else 0.)
                              +(p['wage_credit_pressure'] if next_regime==3 else 0.))
                s['labor_slack']=p['wage_slack_memory']*o['labor_slack']+(1-p['wage_slack_memory'])*target_slack
                s['wage_potential_growth']=p['wage_growth_memory']*o['wage_potential_growth']+(1-p['wage_growth_memory'])*wg
                s['wage_potential_log']=o['wage_potential_log']+s['wage_potential_growth']
                # Persistent pressure lowers the target wage LEVEL. It does
                # not subtract a negative growth drift forever. As labor slack
                # clears, the gap closes gradually without resetting wages.
                wage_gap=p['wage_pressure_level_years']*o['labor_slack']
                level_error=o['wage_potential_log']-wage_gap-o['wage_log']
                target_growth=s['wage_potential_growth']+p['wage_level_correction']*level_error
                adjustment=p['wage_increase_adjustment'] if target_growth>o['wage_growth'] else p['wage_decrease_adjustment']
                s['wage_growth']=o['wage_growth']+adjustment*(target_growth-o['wage_growth'])
            else:
                s['wage_growth']=p['wage_growth_memory']*o['wage_growth']+(1-p['wage_growth_memory'])*wg
            s['wage_log']=o['wage_log']+s['wage_growth']+x('wage_log')
            s['last_passenger_cycle_log']=pc;s['last_freight_cycle_log']=fc
            s['energy_log']=p['regional_energy_memory']*o['energy_log']+p['regional_energy_cycle_log']*s['cycle']+p['regional_energy_noise_log']*rz[6]+x('energy_log')
            s['materials_log']=p['regional_materials_memory']*o['materials_log']+p['regional_materials_industry_log']*s['industry']+p['regional_materials_noise_log']*rz[7]+x('materials_log')
            if local:
                s['energy_log']+=(1-p['regional_energy_memory'])*local['energy']
                s['materials_log']+=(1-p['regional_materials_memory'])*local['materials']
            vals=dict(energy_real_index=base*safe_exp(r['energy_pass_through']*(national['energy_log']+national['energy_secular'])+s['energy_log']),
                wage_real_index=base*safe_exp(s['wage_log']),
                materials_real_index=base*safe_exp(r['materials_beta']*(national['materials_log']+national['materials_secular'])+s['materials_log']),
                real_rate_pct=national['rate'],passenger_demand_index=base*safe_exp(s['ptrend']+pc),
                freight_demand_index=base*safe_exp(s['ftrend']+fc),valuation_index=national['valuation_index'])
            emit(t,r,s,vals,gp,gf,pc,fc)
        if shock:
            events.append(dict(year_index=t,calendar_year=start_year+t,event_type='diagnostic_override',
                          region=','.join(shock.get('regions',list(reg))),magnitude=0.,description=json.dumps(shock,ensure_ascii=False)))
        emit_factor(t)
    # Output region order is the contract order, not internal iteration order.
    order={rid:i for i,rid in enumerate(['northeast','north','northwest','southwest','south','central','east','southeast'])}
    rows.sort(key=lambda row:(row['year_index'],order[row['region_id']]))
    return dict(metadata=dict(model_version=cfg['schema_version'],seed=seed,years=years,base_year=start_year,
        observations_per_series=years+1,regions=8,regional_series=40,national_series=2,unique_series=42,
        display_columns=56,national_pe_series=1,
        price_basis=cfg['price_basis'],config_sha256=config_hash(cfg),reference_commit=cfg['reference_commit'],
        empirical_calibration=False,original_airport_engine_executed=False,
        index_metrics=INDEX_METRICS,nonindex_metric='real_rate_pct',
        unique_regional_metrics=REGIONAL_METRICS,unique_national_metrics=NATIONAL_METRICS),rows=rows,national_factors=factors,events=events)

def public_snapshot(rows:list[dict[str,Any]],current_year_index:int)->list[dict[str,Any]]:
    """Return only released, public fields. Do not expose future rows or latent states."""
    fields=['year_index','calendar_year','region_id','region_name',*CORE_METRICS,'pe_multiple']
    if current_year_index<0:
        raise ValueError('current_year_index must be nonnegative.')
    return [{k:r[k] for k in fields} for r in rows if r['year_index']<=current_year_index]

def public_market_snapshot(result:dict[str,Any], current_year_index:int)->dict[str,Any]:
    """Game-facing boundary: never expose future years, event RNG, latent macro states."""
    if current_year_index<0:
        raise ValueError('current_year_index must be nonnegative')
    rows=public_snapshot(result['rows'],current_year_index)
    national=[{
       'year_index':n['year_index'],'calendar_year':n['calendar_year'],
       'real_rate_pct':n['rate'],'pe_multiple':safe_exp(n['logpe']),
       'valuation_index':n['valuation_index']
    } for n in result['national_factors'] if n['year_index']<=current_year_index]
    return {'metadata':{'model_version':result['metadata']['model_version'],
           'current_year_index':current_year_index},
            'regional_rows':rows,'national_rows':national}

def write_csv(path:Path, rows:list[dict[str,Any]], fields:list[str]|None=None)->None:
    fields=fields or (list(rows[0]) if rows else [])
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def export_result(result:dict[str,Any],out:Path)->None:
    out.mkdir(parents=True,exist_ok=True)
    rows=result['rows']; years=result['metadata']['years']
    write_csv(out/'annual_long.csv',rows)
    write_csv(out/'national_factors_INTERNAL.csv',result['national_factors'])
    national_rows=[{'year_index':n['year_index'],'calendar_year':n['calendar_year'],
                    'real_rate_pct':n['rate'],'pe_multiple':safe_exp(n['logpe']),
                    'valuation_index':n['valuation_index']} for n in result['national_factors']]
    write_csv(out/'national_finance.csv',national_rows)
    write_csv(out/'events.csv',result['events'],['year_index','calendar_year','event_type','region','magnitude','description'])
    order=list(dict.fromkeys(r['region_id'] for r in rows))
    lookup={(r['year_index'],r['region_id']):r for r in rows}
    wide=[]
    for t in range(years+1):
        row={'year_index':t,'calendar_year':result['metadata']['base_year']+t}
        for metric in REGIONAL_METRICS:
            for rid in order:
                row[f'{rid}__{metric}']=lookup[t,rid][metric]
        row['national__real_rate_pct']=national_rows[t]['real_rate_pct']
        row['national__valuation_index']=national_rows[t]['valuation_index']
        wide.append(row)
    write_csv(out/'annual_wide_42.csv',wide)
    # Display adapter repeats the NATIONAL values for each region; DO NOT treat as 56 independent paths.
    display=[]
    for t in range(years+1):
        row={'year_index':t,'calendar_year':result['metadata']['base_year']+t}
        for metric in CORE_METRICS:
            for rid in order:
                row[f'{rid}__{metric}']=lookup[t,rid][metric]
        display.append(row)
    write_csv(out/'annual_wide_56_display_only.csv',display)
    (out/'scenario.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'public_history_y10_example.json').write_text(json.dumps(public_market_snapshot(result,min(10,years)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for metric in REGIONAL_METRICS:
        metricrows=[{'year_index':t,'calendar_year':result['metadata']['base_year']+t,
                    **{rid:lookup[t,rid][metric] for rid in order}} for t in range(years+1)]
        write_csv(out/(metric+'.csv'),metricrows)

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,default=ROOT/'config.json')
    ap.add_argument('--years',type=int,default=60)
    ap.add_argument('--seed',type=int,default=20261014)
    ap.add_argument('--start-year',type=int,default=None)
    ap.add_argument('--out',type=Path,default=ROOT.parents[1]/'railway_economy_output'/'macro')
    a=ap.parse_args(); result=simulate(load_config(a.config),years=a.years,seed=a.seed,start_year=a.start_year)
    export_result(result,a.out)
    print(json.dumps(result['metadata'],ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
