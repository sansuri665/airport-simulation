"""A scenario-only bureau-specific exposure layer on railway-real-macro-v0.5.

All numbers are explicitly hypothetical. Actual industry finances and route OD
allocations are not inferred from map geometry. No volume caps, no unearned annual
productivity improvement, no maintenance ageing, no financing or commercial assets.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import math, random
from typing import Mapping, Any

REGION_ORDER = ('northeast','north','northwest','southwest','south','central','east','southeast')
# PLACEHOLDERS. Replace with 2025 railway passenger-km and tonne-km weights.
NATIONAL_WEIGHTS_P = dict(zip(REGION_ORDER, (.07,.17,.06,.12,.18,.13,.19,.08)))
NATIONAL_WEIGHTS_F = dict(zip(REGION_ORDER, (.13,.16,.13,.08,.13,.15,.14,.08)))

@dataclass(frozen=True)
class Exposure:
    bureau_id: str
    name: str
    region_id: str = 'northeast'
    passenger_local_weight: float = .75
    freight_local_weight: float = .70
    passenger_trend_beta: float = 1.
    freight_trend_beta: float = 1.
    passenger_cycle_beta: float = 1.
    freight_cycle_beta: float = 1.
    passenger_local_drift_year: float = 0.
    freight_local_drift_year: float = 0.
    passenger_drift_vol: float = .004
    freight_drift_vol: float = .004
    passenger_cycle_vol: float = .012
    freight_cycle_vol: float = .017
    energy_price_beta: float = 1.
    wage_price_beta: float = 1.
    materials_price_beta: float = 1.

def validate_profile(p: Exposure):
    for w in (p.passenger_local_weight,p.freight_local_weight):
        if not 0<=w<=1:raise ValueError('local demand weight must be in [0,1]')
    for x in (p.passenger_trend_beta,p.freight_trend_beta,p.passenger_cycle_beta,p.freight_cycle_beta,
              p.energy_price_beta,p.wage_price_beta,p.materials_price_beta):
        if not 0<x<4:raise ValueError('invalid elasticity')
    for x in (p.passenger_drift_vol,p.freight_drift_vol,p.passenger_cycle_vol,p.freight_cycle_vol):
        if not 0<=x<=.1:raise ValueError('excessive simulated local variance')


def national_factors(rows:Mapping[str,dict[str,Any]]) -> dict[str,dict[str,float]]:
    """Decompose national aggregate to trend and cycle without peeking ahead.

    NOTE: simple weighted aggregation uses assumed *base-year* OD weights.
    """
    if set(rows)!=set(REGION_ORDER):raise ValueError('exactly eight regions required')
    result={}
    for typ, w in [('passenger',NATIONAL_WEIGHTS_P),('freight',NATIONAL_WEIGHTS_F)]:
        trend=sum(w[r]*math.exp(rows[r][typ+'_trend_log']) for r in REGION_ORDER)
        observed=sum(w[r]*rows[r][typ+'_demand_index']/100 for r in REGION_ORDER)
        result[typ]={'trend':trend,'cycle':observed/trend,'total':observed}
    return result


def bureau_specific_states(p:Exposure,seed:int,years:int=60)->list[dict[str,float]]:
    """Independent, slow-varying subregional trend plus temporary local cycles.

    Targets last 10-18 years, but no future information is used by the
    calculate-one-year API. Phase planner only belongs to the scenario engine.
    """
    validate_profile(p)
    s=sha256(f'rail-bureau-differentiation-v01|{seed}|{p.bureau_id}'.encode()).digest()
    rng=random.Random(int.from_bytes(s[:16],'big'))
    out=[{'passenger_trend_log':0.,'freight_trend_log':0.,'passenger_cycle_log':0.,'freight_cycle_log':0.}]
    annual={'passenger':p.passenger_local_drift_year,'freight':p.freight_local_drift_year}
    level={'passenger':0.,'freight':0.}
    temporary={'passenger':0.,'freight':0.}
    remaining=0;targets={}
    for t in range(1,years+1):
        if remaining<=0:
            remaining=rng.randint(10,18)
            targets={
                'passenger': p.passenger_local_drift_year + rng.gauss(0,p.passenger_drift_vol),
                'freight': p.freight_local_drift_year + rng.gauss(0,p.freight_drift_vol),
            }
        for key,vol in [('passenger',p.passenger_cycle_vol),('freight',p.freight_cycle_vol)]:
            annual[key]=.78*annual[key]+.22*targets[key]
            level[key]+=annual[key]
            temporary[key]=.75*temporary[key]+vol*rng.gauss(0,1)
        out.append({k+'_trend_log':level[k] for k in ('passenger','freight')}|
                   {k+'_cycle_log':temporary[k] for k in ('passenger','freight')})
        remaining-=1
    return out


def compute_transport_index(p:Exposure, regional:dict[str,Any],
                            national:dict[str,dict[str,float]],
                            private_state:dict[str,float])->dict[str,float]:
    """Uncapped volume indices relative to 2025. Trend/cycle betas distinct."""
    validate_profile(p)
    result={}
    for typ in ('passenger','freight'):
        weight=getattr(p,typ+'_local_weight')
        local_trend=regional[typ+'_trend_log']
        local_cycle=regional[typ+'_cycle_log']
        nat= national[typ]
        long_change=weight*local_trend+(1-weight)*math.log(nat['trend'])
        cyc_change=weight*local_cycle+(1-weight)*math.log(nat['cycle'])
        loglevel=(getattr(p,typ+'_trend_beta')*long_change +
                  getattr(p,typ+'_cycle_beta')*cyc_change +
                  private_state[typ+'_trend_log']+private_state[typ+'_cycle_log'])
        if not math.isfinite(loglevel) or abs(loglevel)>150:raise ValueError('unstable demand')
        result[typ+'_index']=100*math.exp(loglevel)
    return result
