"""Off-map net freight receipts. Equivalent settlement tonnes stay separate.

The receipts have already had external direct expenses deducted. They never
enter the operating workload, station income, map geometry or ordinary tonnes.
"""
from __future__ import annotations

import copy
import math
from .revenue import CURRENT_POLICY, unit_yield, validate_policy

VERSION = 'railway-freight-settlement-v0.2-independent'


def validate_hidden_freight(rec: dict | None) -> None:
    if rec is None:
        return
    for key in ('base_net_receipts_yi', 'base_equivalent_tons_10k', 'accounting_yield_yuan_per_ton', 'demand_beta', 'settlement_scale'):
        v = rec[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f'Invalid hidden freight {key}')
    if rec['accounting_yield_yuan_per_ton'] <= 0 or rec['demand_beta'] != 1 or rec['settlement_scale'] > 1:
        raise ValueError('Expected positive yield, linear freight driver and scale in 0..1')
    if rec['volume_driver'] != 'bureau_freight_index':
        raise ValueError('Hidden freight must follow the existing bureau freight index')
    for key in ('extra_modeled_cost_yi', 'station_income_increment_yi'):
        if rec[key] != 0:
            raise ValueError('Net settlement must not add expenses or station income')
    if not math.isclose(rec['base_equivalent_tons_10k'] * rec['accounting_yield_yuan_per_ton'] / 10000,
                        rec['base_net_receipts_yi'], abs_tol=1e-9, rel_tol=1e-10):
        raise ValueError('Settlement tonnes and base receipts do not reconcile')


def apply_hidden_freight(core: dict, profile: dict, *, revenue_policy: dict | None = None) -> dict:
    if core.get('freight_settlement_applied'):
        raise ValueError('Do not apply net freight settlement twice')
    rec = profile.get('hidden_freight')
    validate_hidden_freight(rec)
    index = core['freight_index']
    if not math.isfinite(index) or index < 0:
        raise ValueError('Invalid freight index')
    factor = index / 100
    policy = validate_policy(CURRENT_POLICY if revenue_policy is None else revenue_policy)
    unit = unit_yield(factor, 'freight', policy) if policy['settlement_uses_freight_yield'] else 1.
    unscaled = rec['base_net_receipts_yi'] * factor * unit if rec else 0.
    hidden = unscaled * rec['settlement_scale'] if rec else 0.
    equivalent = hidden * 10000 / rec['accounting_yield_yuan_per_ton'] if rec else 0.
    if not all(math.isfinite(v) for v in (hidden, unscaled, equivalent)):
        raise ValueError('Nonfinite net settlement')
    result = copy.deepcopy(core)
    result.update({
        'freight_settlement_applied': True,
        'ordinary_freight_tons_10k': core['freight_tons_10k'],
        'ordinary_freight_income_yi': core['freight_income_yi'],
        'hidden_equivalent_freight_tons_10k': equivalent,
        'hidden_freight_income_yi': hidden,
        'unscaled_hidden_freight_income_yi': unscaled,
        'settlement_unit_yield_factor': unit,
        'settlement_base_net_yi': rec['base_net_receipts_yi'] * rec['settlement_scale'] if rec else 0.,
        'core_operating_surplus_yi': core['operating_surplus_yi'],
        'core_revenue_yi': core['revenue_yi'],
        'freight_income_yi': core['freight_income_yi'] + hidden,
        'revenue_yi': core['revenue_yi'] + hidden,
        'operating_surplus_yi': core['operating_surplus_yi'] + hidden,
    })
    # freight_tons_10k remains physical ordinary volume. Do NOT add equivalent
    # settlement tonnes, or feed them back into finance() as freight workload.
    for name in ('v02', 'full'):
        result[name + '_operating_surplus_yi'] += hidden
    return result
