(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const query = new URLSearchParams(location.search);
  const inputs = [['energy', '能源', '#83c6dc'], ['wage', '人工', '#dca872'], ['materials', '材料', '#b8a0d1'], ['other', '其他', '#93d2c6']];
  const segments = [['high_speed', '高速'], ['conventional', '普速'], ['station', '站务']];
  const views = {
    accounts: {title: '经营收支', unit: '亿元／年 · 2025 年不变价', series: [['revenue_yi', '总收入', '#83c6dc'], ['cost_yi', '总成本', '#dca872'], ['operating_surplus_yi', '经营结余', '#93d2c6']]},
    inputs: {title: '四项投入成本', unit: '亿元／年 · 2025 年不变价', series: inputs.map(([k, n, c]) => [k + '_cost_yi', n, c])},
    volumes: {title: '客货运业务规模', unit: '本分局 2025 年 = 100', series: [['passenger_index', '客运量指数', '#83c6dc'], ['freight_index', '货运量指数', '#dca872']]},
    labor: {title: '人工成本 · 三组对照', unit: '亿元／年 · 同一业务量', series: [['v02_wage_cost_yi', 'A 原 V0.2', '#dca872', '5 4'], ['full_wage_cost_yi', 'B 工资完全传导', '#b8a0d1', '3 4'], ['wage_cost_yi', 'C 当前规则', '#93d2c6']]},
    freight: {title: '货运收入构成', unit: '亿元／年 · 含净结算', series: [['ordinary_freight_income_yi','普通货运收入','#83c6dc'],['hidden_freight_income_yi','隐藏净结算','#dca872'],['freight_income_yi','货运收入合计','#93d2c6']]},
    cash: {title: '现金、年度补资与分红', unit: '亿元 · 2025 年不变价', series: [['cash_opening_yi','期初可用现金','#dca872','5 4'],['cash_closing_yi','期末现金','#83c6dc'],['cash_state_equity_yi','本年度增资（上年末到账）','#93d2c6'],['cash_dividend_yi','年末分红','#b8a0d1']]},
    cash_compare: {title: '分红前后现金积累',unit:'亿元 · 相同 Seed 与经营路径',series:[['cash_without_dividends_closing_yi','不分红参考现金','#dca872','5 4'],['cash_closing_yi','分红后现金','#83c6dc']]},
    valuation: {title:'国铁官方估值与完整未来参考',unit:'亿元 · 全公司股权',series:[['valuation_official_yi','国铁官方估值','#83c6dc'],['valuation_full_future_reference_yi','完整未来参考估值','#dca872','5 4'],['valuation_cash_yi','公司现金','#93d2c6']]}
  };
  const valuationColumns=[['year','年份'],['valuation_official_yi','官方股权估值'],['valuation_full_future_reference_yi','完整未来参考估值'],['valuation_operating_right_yi','经营权现值'],['valuation_cash_yi','公司现金'],['valuation_old_share_ask_yi','旧股卖价（全公司）'],['valuation_old_share_state_bid_yi','国铁旧股买价（全公司）'],['valuation_issue_pre_yi','增资投前报价'],['valuation_forecast_score','十年预测评分']];
  const cashColumns = [['year','经营年度'],['cash_funding_year','增资到账年份（年末）'],['cash_carryover_yi','上年结转现金（补资前）'],['cash_state_equity_yi','本年度国铁增资'],['cash_opening_yi','期初可用现金'],['cash_operating_proxy_yi','当年经营结余现金近似'],['cash_dividend_yi','年末分红'],['cash_closing_yi','年末现金'],['cash_cumulative_equity_yi','累计国铁增资'],['cash_cumulative_dividend_yi','累计分红'],['cash_cumulative_state_net_investment_yi','累计国铁净投入']];
  const annualColumns = [['year', '年份'], ['passenger_trips_10k', '客运量（万人次）'], ['ordinary_freight_tons_10k', '普通货运量（万吨）'], ['hidden_equivalent_freight_tons_10k','隐藏等效结算量（万吨）'], ['passenger_income_yi', '客运收入'], ['ordinary_freight_income_yi','普通货运收入'], ['hidden_freight_income_yi','隐藏货运净结算'], ['freight_income_yi', '货运收入合计'], ['station_income_yi', '站务收入'], ['high_speed_cost_yi', '高速成本'], ['conventional_cost_yi', '普速成本'], ['station_cost_yi', '站务成本'], ['revenue_yi', '总收入'], ['cost_yi', '总成本'], ['operating_surplus_yi', '经营结余']];
  let catalog = null, data = null, busy = false, chartCursor = null, chartX = null;
  let view = Object.hasOwn(views, query.get('view')) ? query.get('view') : 'accounts';
  let year = /^\d{4}$/.test(query.get('year') || '') ? Math.max(2025, Math.min(2085, Number(query.get('year')))) : 2085;
  const cache = new Map();
  const ns = 'http://www.w3.org/2000/svg';
  const node = (tag, text, className) => {const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el;};
  const svgNode = (tag, attributes = {}, text) => {const el = document.createElementNS(ns, tag); for (const [k, v] of Object.entries(attributes)) el.setAttribute(k, v); if (text !== undefined) el.textContent = text; return el;};
  const fixed = (n, digits = 2) => n.toLocaleString('zh-CN', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const signClass = n => n < 0 ? 'negative' : n > 0 ? 'positive' : '';
  function setSigned(el, n) {el.textContent = fixed(n); el.classList.remove('negative', 'positive'); if (signClass(n)) el.classList.add(signClass(n));}
  function status(text, error = false) {$('bureauStatus').textContent = text; $('bureauStatus').classList.toggle('error', error);}
  function disable(value) {busy = value; for (const id of ['bureauRegion', 'bureauSelect', 'bureauSeed', 'runBureau', 'randomBureau']) $(id).disabled = value;}
  function seedValue() {
    const text = $('bureauSeed').value.trim();
    const seed = /^\d{1,16}$/.test(text) ? Number(text) : NaN;
    if (!Number.isSafeInteger(seed) || seed < 0) throw new Error('请输入 0—9,007,199,254,740,991 之间的整数种子。');
    return seed;
  }
  function populateBureaus(preferred) {
    const available = catalog.bureaus.filter(b => b.region_id === $('bureauRegion').value);
    $('bureauSelect').replaceChildren(...available.map(b => {const option = node('option', b.name + '铁路分局'); option.value = b.bureau_id; return option;}));
    if (available.some(b => b.bureau_id === preferred)) $('bureauSelect').value = preferred;
  }
  function syncLocation() {
    if (!data) return;
    const url = new URL(location.href);
    for (const [k, v] of Object.entries({region: data.profile.region_id, bureau: data.profile.bureau_id, seed: data.seed, year, view})) url.searchParams.set(k, v);
    window.history.replaceState(null, '', url);
    $('macroLink').href = `./economy.html?division=${encodeURIComponent(data.profile.bureau_id)}&region=${data.profile.region_id}&seed=${data.seed}&year=${year}`;
  }
  function renderYear() {
    if (!data) return;
    const row = data.rows[year - data.baseYear], base = data.rows[0];
    $('bureauYear').value = year; $('bureauYearLabel').textContent = year;
    $('surplusLabel').textContent = `${year} 年经营结余`;
    setSigned($('yearSurplus'), row.operating_surplus_yi);
    $('yearRevenue').textContent = fixed(row.revenue_yi); $('yearCost').textContent = fixed(row.cost_yi);
    const change = (value, baseline) => {const delta = (value / baseline - 1) * 100; return `亿元 · 较基期 ${delta >= 0 ? '+' : ''}${fixed(delta, 1)}%`;};
    $('revenueChange').textContent = change(row.revenue_yi, base.revenue_yi);
    $('costChange').textContent = change(row.cost_yi, base.cost_yi);
    $('costTitle').textContent = `${year} 年成本结构`;
    const composition = document.createDocumentFragment();
    for (const [kind, label, color] of inputs) {
      const value = row[kind + '_cost_yi'];
      const f = segments.reduce((sum, [s]) => sum + row.cost_breakdown[s][kind].fixed_cost_yi, 0);
      const wrap = node('div', undefined, 'input-row');
      const heading = node('div', undefined, 'input-label'), amount = node('b', fixed(value));
      amount.append(node('small', `${fixed(value / row.cost_yi * 100, 1)}%`));
      heading.append(node('span', label), amount);
      const track = node('div', undefined, 'input-track'); track.style.setProperty('--input-color', color);
      track.setAttribute('aria-label', `${label}：固定 ${fixed(f)} 亿元，变动 ${fixed(value - f)} 亿元`);
      const a = node('i'), b = node('i'); a.style.width = `${value ? f / value * 100 : 0}%`; b.style.width = `${value ? (1 - f / value) * 100 : 0}%`;
      track.append(a, b); wrap.append(heading, track); composition.append(wrap);
    }
    $('inputComposition').replaceChildren(composition);
    $('fixedReadout').textContent = `固定支出 ${fixed(row.fixed_operating_cost_yi)} 亿元，占 ${fixed(row.fixed_operating_cost_yi / row.cost_yi * 100, 1)}%；其余为随业务量变化的支出。`;
    $('passengerVolume').textContent = `${fixed(row.passenger_trips_10k)} 万人次`;
    $('freightVolume').textContent = `${fixed(row.ordinary_freight_tons_10k)} 万吨`;
    const settlement = data.profile.hidden_freight;
    $('hiddenVolumeRow').hidden = !settlement;
    $('hiddenFreightPanel').hidden = !settlement;
    $('hiddenFreightVolume').textContent = `${fixed(row.hidden_equivalent_freight_tons_10k)} 万吨`;
    if (settlement) {
      $('hiddenFreightTitle').textContent = `${year} 年 · 地图外货运净结算`;
      $('settlementScale').textContent = `独立结算 · 基值权重 ${fixed(settlement.settlement_scale*100,0)}%`;
      $('ordinaryFreightIncome').textContent = `${fixed(row.ordinary_freight_income_yi)} 亿元`;
      $('hiddenFreightIncome').textContent = `${fixed(row.hidden_freight_income_yi)} 亿元`;
      $('totalFreightIncome').textContent = `${fixed(row.freight_income_yi)} 亿元`;
      $('settlementReadout').textContent = `配置基期净结算 ${fixed(settlement.base_net_receipts_yi)} 亿元／年，当前基值 ${fixed(settlement.base_net_receipts_yi*settlement.settlement_scale)} 亿元／年；当年货运指数 ${fixed(row.freight_index,1)}，单位净收益系数 ${fixed(row.settlement_unit_yield_factor,3)}。普通货运量 ${fixed(row.ordinary_freight_tons_10k)} 万吨，另有隐藏等效结算量 ${fixed(row.hidden_equivalent_freight_tons_10k)} 万吨。`;
    }
    $('laborTitle').textContent = `${year} 年人工成本对照`;
    $('wagePeakReadout').textContent = `地区工资 ${fixed(row.regional_wage_index, 1)} · 历史高点 ${fixed(row.historical_wage_peak_index, 1)}（2025 = 100）`;
    $('laborBefore').textContent = `${fixed(row.v02_wage_cost_yi)} 亿元`;
    $('laborFull').textContent = `${fixed(row.full_wage_cost_yi)} 亿元`;
    $('laborAfter').textContent = `${fixed(row.wage_cost_yi)} 亿元`;
    const laborChange = row.wage_cost_yi - row.v02_wage_cost_yi;
    $('laborEffect').textContent = `高点调整使人工支出相对 B 减少 ${fixed(row.full_wage_cost_yi-row.wage_cost_yi)} 亿元；相对 A 的净变化为 ${laborChange>=0?'+':''}${fixed(laborChange)} 亿元。三组运量、收入和非人工支出相同。`;
    $('laborTheta').textContent = `θ：${segments.map(([s,n])=>`${n} ${fixed(data.profile.cost_inputs[s].wage.labor_adjustment_theta)}`).join(' · ')}。工资回落时保留已积累的调整，仅在工资创历史新高时进一步调整。`;
    $('detailTitle').textContent = `${year} 年 · 十二项成本明细`;
    const details = document.createDocumentFragment();
    for (const [s, name] of segments) inputs.forEach(([kind, label], i) => {
      const c = row.cost_breakdown[s][kind], tr = node('tr');
      if (i === 0) tr.className = 'segment-start';
      const th = node('th', `${name} / ${label}`); th.scope = 'row'; tr.append(th);
      for (const key of ['fixed_cost_yi', 'variable_cost_yi', 'cost_yi', 'price_factor', 'unit_cost_factor', 'workload_factor']) tr.append(node('td', fixed(c[key], 3)));
      details.append(tr);
    });
    $('costDetailRows').replaceChildren(details);
    for (const tr of $('annualRows').children) {
      const selected = Number(tr.dataset.year) === year;
      tr.classList.toggle('selected-year', selected);
      if (selected) tr.querySelector('button').setAttribute('aria-current', 'true'); else tr.querySelector('button').removeAttribute('aria-current');
    }
    renderCashYear(row);
    renderValuationYear(row);
    if (chartCursor && chartX) {const x = chartX(year); chartCursor.setAttribute('x1', x); chartCursor.setAttribute('x2', x);}
    const target = $('bureauChart').querySelector('.chart-inspection-target');
    if (target) {target.setAttribute('aria-valuenow', year); target.setAttribute('aria-valuetext', `${year} 年`);}
    syncLocation();
  }
  function selectYear(value) {year = Math.max(2025, Math.min(2085, Math.round(value))); renderYear();}
  function syncView() {
    const cash = view === 'cash' || view === 'cash_compare';
    const valuation = view === 'valuation';
    for (const id of ['operatingSummary','bureauCostPanel','laborPanel','costDetailPanel','operatingAnnualPanel','operatingConfig','calibrationPanel']) $(id).hidden = cash || valuation;
    for (const id of ['cashSummary','cashNotesPanel','cashDividendPanel','cashLedgerPanel','cashAuditPanel']) $(id).hidden = !cash;
    for (const id of ['valuationSummary','valuationNotesPanel','valuationQuotePanel','valuationForecastPanel','valuationAnnualPanel']) $(id).hidden = !valuation;
    $('hiddenFreightPanel').hidden = cash || valuation || !data.profile.hidden_freight;
  }
  function renderValuationYear(row) {
    for(const [id,key] of [['valuationOfficial','valuation_official_yi'],['valuationRight','valuation_operating_right_yi'],['valuationCash','valuation_cash_yi'],['valuationNext','valuation_next_surplus_forecast_yi']]) {
      $(id).textContent=fixed(row[key]); $(id).classList.toggle('negative',row[key]<0);
    }
    $('valuationNextNote').textContent=`${year+1} 年 · 一年期研究评分 ${fixed(row.valuation_one_year_score,1)}`;
    $('valuationRate').textContent=`${fixed(row.valuation_discount_rate_pct,1)}%`;
    $('valuationNormalized').textContent=`${fixed(row.valuation_historical_normalized_surplus_yi)} 亿元`;
    $('valuationTarget').textContent=`${row.valuation_quality_target} 分`;
    $('valuationScore').textContent=`${fixed(row.valuation_forecast_score,1)} 分`;
    $('valuationCover').textContent=`${fixed(row.valuation_cash_cover_months,1)} 个月`;
    $('valuationBasisNote').textContent=`${year}年末估值。${row.valuation_tail_years?`窗口中${row.valuation_tail_years}年采用末年延续假设。`:'十年窗口全部位于现有模拟样本内。'}${row.valuation_at_floor?'预测经营权与现金合计为负，股权参考值取0。':''}`;
    const bands={comfortable:'现金充足',watch:'现金偏紧',strained_before_formal_crisis:'资金紧迫（未认定危机）'};
    $('valuationBand').textContent=bands[row.valuation_active_band];
    $('valuationQuoteTitle').textContent=`${year} 年末 · 国铁公开报价`;
    $('valuationAsk').textContent=`${fixed(row.valuation_old_share_ask_yi)} 亿元`;
    $('valuationBid').textContent=`${fixed(row.valuation_old_share_state_bid_yi)} 亿元`;
    $('valuationIssue').textContent=`${fixed(row.valuation_issue_pre_yi)} 亿元`;
    $('valuationAskUnit').textContent=`每0.25%股权 ${fixed(row.valuation_old_share_ask_per_unit_yi,4)} 亿元 · 105%`;
    $('valuationBidUnit').textContent=`每0.25%股权 ${fixed(row.valuation_old_share_state_bid_per_unit_yi,4)} 亿元 · 60% · 始终承接`;
    $('valuationIssueNote').textContent=`投前估值 · ${bands[row.valuation_active_band]}档 × ${fixed(row.valuation_issue_multiplier*100,0)}%`;
    $('valuationForecastTitle').textContent=`${year+1}—${year+10} 年经营结余预测`;
    $('valuationForecastNote').textContent=`目标${row.valuation_quality_target}分；十年研究评分${fixed(row.valuation_forecast_score,1)}分，平均归一化偏差${fixed(row.valuation_normalized_error_pct,2)}%。同一估值时点的预测锁定。`;
    const fragment=document.createDocumentFragment();
    for(const f of row.forecastRows) {
      const tr=node('tr');
      for(const text of [String(f.year),fixed(f.predicted_surplus_yi),fixed(f.reference_surplus_yi),`${fixed(Math.abs(f.predicted_surplus_yi-f.reference_surplus_yi)/f.error_scale_yi*100,2)}%`,f.sample_extension?'末年延续假设':'模拟未来']) tr.append(node('td',text));
      fragment.append(tr);
    }
    $('valuationForecastRows').replaceChildren(fragment);
    for(const tr of $('valuationAnnualRows').children) tr.classList.toggle('selected-year',Number(tr.dataset.year)===year);
  }
  function renderValuation() {
    const fragment=document.createDocumentFragment();
    for(const r of data.rows) {
      const tr=node('tr'); tr.dataset.year=r.year;
      const th=node('th'),button=node('button',r.year);th.scope='row';button.type='button';button.dataset.year=r.year;button.setAttribute('aria-label',`查看 ${r.year} 年国铁估值`);th.append(button);tr.append(th);
      for(const [key] of valuationColumns.slice(1)) tr.append(node('td',fixed(r[key])));
      fragment.append(tr);
    }
    $('valuationAnnualRows').replaceChildren(fragment);
  }
  function renderCashYear(row) {
    $('cashInitial').textContent = fixed(row.cash_initial_yi);
    $('cashClosingLabel').textContent = `${year} 年期末现金`;
    setSigned($('cashClosing'),row.cash_closing_yi);
    $('cashEquity').textContent = fixed(row.cash_state_equity_yi);
    $('cashEquityLabel').textContent = `${year} 年度国铁增资`;
    $('cashEquityTiming').textContent = year===2025 ? '基期快照 · 尚无年度增资' : `${row.cash_funding_year} 年末到账 · 亿元`;
    $('cashTiming').textContent = year===2025 ? '2025行为开局快照；2026年度增资在2025年末到账，列入2026行。' : `${year} 年度窗口：${row.cash_funding_year} 年末到账，依据 ${row.cash_estimate_basis_year} 年已知的成本与盈亏。`;
    $('cashCumulative').textContent = fixed(row.cash_cumulative_equity_yi);
    $('cashYearDividend').textContent = fixed(row.cash_dividend_yi);
    $('cashCumulativeDividend').textContent = fixed(row.cash_cumulative_dividend_yi);
    $('cashNetInvestment').textContent = fixed(row.cash_cumulative_state_net_investment_yi);
    $('cashWithoutDividend').textContent = fixed(row.cash_without_dividends_closing_yi);
    $('dividendTitle').textContent = `${year} 年末分红`;
    for(const [id,key] of [['dividendProfit','cash_profit_dividend_yi'],['dividendExcess','cash_excess_dividend_yi'],['dividendReserve','cash_dividend_minimum_yi']]) $(id).textContent = `${fixed(row[key])} 亿元`;
    const dividendStatus={base_snapshot:'基期只初始化，不分红',disabled:'当前关闭分红',received_budget_year_equity:'本年度接受过国铁增资，不分红',nonpositive_operating_surplus:'本年度无正经营结余，不分红',insufficient_cash_reserve:'现金未超过最低保留额，不分红',paid:'本年度分红已支付'};
    $('dividendReadout').textContent = `${dividendStatus[row.cash_dividend_status]}。分红前现金 ${fixed(row.cash_closing_before_dividends_yi)} 亿元；充裕现金线 ${fixed(row.cash_dividend_comfortable_yi)} 亿元。分红在本年经营结算后、下一年度增资前支付。`;
    $('cashFundedYears').textContent = `亿元 · 已有 ${row.cash_injection_years} 个年度补资`;
    $('cashRisk').textContent = year === 2025 ? '亿元 · 基期仅初始化' : row.cash_closing_yi < 0 ? '资金缺口 · 期末现金为负' : row.cash_carryover_yi < 0 ? '上年结转存在资金缺口' : '亿元 · 经营及分红后';
    $('cashRisk').classList.toggle('negative',row.cash_carryover_yi < 0 || row.cash_closing_yi < 0);
    for (const [id,key] of [['cashBefore','cash_carryover_yi'],['cashProjected','cash_projected_closing_before_funding_yi'],['cashTrigger','cash_trigger_yi'],['cashTarget','cash_target_yi'],['cashExpectedLoss','cash_expected_loss_yi']]) {
      $(id).textContent = year===2025 && id!=='cashBefore' ? '—' : `${fixed(row[key])} 亿元`; $(id).classList.toggle('negative',year>2025 && row[key] < 0);
    }
    for (const tr of $('cashLedgerRows').children) {
      const selected = Number(tr.dataset.year) === year;
      tr.classList.toggle('selected-year',selected);
      if (selected) tr.querySelector('button').setAttribute('aria-current','true'); else tr.querySelector('button').removeAttribute('aria-current');
    }
    syncView();
  }
  function renderCash() {
    const rows = document.createDocumentFragment();
    for (const row of data.rows) {
      const tr = node('tr'); tr.dataset.year = row.year;
      const th = node('th'), button = node('button',row.year); th.scope='row'; button.type='button'; button.dataset.year=row.year; button.setAttribute('aria-label',`查看 ${row.year} 年现金`); th.append(button); tr.append(th);
      for (const [key] of cashColumns.slice(1)) {const td=node('td',key==='cash_funding_year' ? (row[key]===null ? '—' : String(row[key])) : fixed(row[key])); if(row[key]<0) td.className='negative'; tr.append(td);}
      rows.append(tr);
    }
    $('cashLedgerRows').replaceChildren(rows);
    const audit = data.cash.calibrationAudit, fragment=document.createDocumentFragment();
    for (const id of ['cashAuditEquity','cashAuditDividend','cashAuditNet','cashAuditCash','cashAuditWithoutCash','cashAuditNegative']) $(id).textContent='—';
    if (audit) {
      const b=audit.bureau, region=catalog.regions.find(r=>r.id===data.profile.region_id);
      $('cashAuditTitle').textContent=`${region.name} · 96 个 Seed 现金与补资`;
      $('cashAuditEquity').textContent=`${fixed(b.cumulative_equity_median_yi)} 亿元`;
      $('cashAuditDividend').textContent=`${fixed(b.cumulative_dividend_median_yi)} 亿元`;
      $('cashAuditNet').textContent=`${fixed(b.cumulative_state_net_investment_median_yi)} 亿元`;
      $('cashAuditCash').textContent=`${fixed(b.ending_cash_median_yi)} 亿元`;
      $('cashAuditWithoutCash').textContent=`${fixed(b.withoutDividends.ending_cash_median_yi)} 亿元`;
      $('cashAuditNegative').textContent=`${fixed(b.ever_negative_closing_fraction*100,1)}%`;
      $('cashAuditNote').textContent=`Seed ${audit.seedRange[0]}—${audit.seedRange[1]}；本区60年累计增资／分红／国铁净投入中位数分别为 ${fixed(audit.region.cumulative_equity_median_yi)}／${fixed(audit.region.cumulative_dividend_median_yi)}／${fixed(audit.region.cumulative_state_net_investment_median_yi)} 亿元（各项分别逐Seed区域加总后取中位数）。`;
      for (const b of audit.bureaus) {
        const tr=node('tr'); if(b.bureau_id===data.profile.bureau_id) tr.className='current-bureau';
        const th=node('th',b.name); th.scope='row'; tr.append(th,node('td',fixed(b.cumulative_dividend_median_yi)),node('td',fixed(b.ending_cash_median_yi)),node('td',fixed(b.withoutDividends.ending_cash_median_yi)),node('td',fixed(b.cumulative_equity_median_yi)),node('td',fixed(b.cumulative_state_net_investment_median_yi)),node('td',fixed(b.injection_years_median,1)),node('td',`${fixed(b.ever_negative_closing_fraction*100,1)}%`)); fragment.append(tr);
      }
    } else $('cashAuditNote').textContent='尚无匹配当前现金配置的96 Seed报告，请重跑现金审计并重启服务。';
    $('cashAuditRows').replaceChildren(fragment);
  }
  function drawChart() {
    if (!data) return;
    const chart = $('bureauChart'), spec = views[view];
    const width = Math.max(320, Math.round(chart.parentElement.getBoundingClientRect().width));
    const height = Math.min(390, Math.max(285, Math.round(width * .42)));
    const left = 60, right = width - 16, top = 24, bottom = height - 37;
    chart.setAttribute('viewBox', `0 0 ${width} ${height}`);
    chart.setAttribute('aria-label', `${data.profile.name}分局，${spec.title}，2025 至 2085 年`);
    const values = spec.series.flatMap(([key]) => data.rows.map(r => r[key]));
    let low = Math.min(0, ...values), high = Math.max(0, ...values);
    const margin = (high - low || 1) * .09; if (low < 0) low -= margin; high += margin;
    const x = y => left + (y - 2025) / 60 * (right - left);
    const y = v => bottom - (v - low) / (high - low) * (bottom - top);
    chartX = x;
    const drawing = document.createDocumentFragment();
    for (let i = 0; i <= 5; i++) {
      const value = low + (high - low) * i / 5, py = y(value);
      drawing.append(svgNode('line', {x1:left, x2:right, y1:py, y2:py, stroke:'#26373e', 'stroke-dasharray':'3 5'}));
      drawing.append(svgNode('text', {x:left - 10, y:py + 4, fill:'#82999f', 'font-size':10, 'text-anchor':'end'}, fixed(value, high - low > 30 ? 0 : 1)));
    }
    drawing.append(svgNode('line', {x1:left, x2:right, y1:y(0), y2:y(0), stroke:'#587076', 'stroke-width':1}));
    for (let value = 2025; value <= 2085; value += width < 500 ? 20 : 10) drawing.append(svgNode('text', {x:x(value), y:height - 12, fill:'#82999f', 'font-size':10, 'text-anchor':'middle'}, value));
    for (const [key, label, color, dash] of spec.series) {
      if (view==='cash' && ['cash_state_equity_yi','cash_dividend_yi'].includes(key)) {
        const barWidth=Math.max(2,(right-left)/61*.55);
        for(const row of data.rows) if(row[key]>0) drawing.append(svgNode('rect',{x:x(row.year)-barWidth/2,y:y(row[key]),width:barWidth,height:y(0)-y(row[key]),fill:color,opacity:.5}));
        continue;
      }
      drawing.append(svgNode('polyline', {points:data.rows.map(r => `${x(r.year)},${y(r[key])}`).join(' '), fill:'none', stroke:color, 'stroke-width':2.1, 'stroke-linejoin':'round', 'stroke-dasharray':dash||'none'}));
      for (const row of data.rows) drawing.append(svgNode('circle', {cx:x(row.year), cy:y(row[key]), r:1.6, fill:color, opacity:.65, 'aria-hidden':'true'}));
    }
    chartCursor = svgNode('line', {x1:x(year), x2:x(year), y1:top, y2:bottom, stroke:'#aac2c4', 'stroke-dasharray':'3 4', opacity:.65, 'pointer-events':'none'});
    const marker = svgNode('g', {visibility:'hidden', 'pointer-events':'none'});
    const guide = svgNode('line', {y1:top, y2:bottom, stroke:'#a4b9bb', 'stroke-width':1}); marker.append(guide);
    const dots = spec.series.map(([, , color]) => svgNode('circle', {r:4, fill:color, stroke:'#101b21', 'stroke-width':2})); marker.append(...dots);
    const target = svgNode('rect', {x:left, y:top, width:right-left, height:bottom-top, fill:'transparent', tabindex:0, role:'slider', class:'chart-inspection-target', 'aria-label':'曲线查看年份', 'aria-valuemin':2025, 'aria-valuemax':2085, 'aria-valuenow':year});
    const tooltip = $('bureauTooltip'); tooltip.hidden = true;
    let hovered = year;
    function inspect(value) {
      hovered = Math.max(2025, Math.min(2085, value)); const row = data.rows[hovered - 2025];
      const title = node('strong', `${hovered} 年`), subtitle = node('span', view === 'volumes' ? '基期 = 100' : view === 'valuation' ? '亿元 · 全公司股权' : (view === 'cash' || view === 'cash_compare') ? '亿元 · 余额 / 当年收支' : '亿元／年');
      const content = [title, subtitle];
      spec.series.forEach(([key, label, color], i) => {
        const line = node('div', undefined, 'chart-tooltip-row'), swatch = node('i'); swatch.style.background = color;
        line.append(swatch, document.createTextNode(label), node('b', fixed(row[key]))); content.push(line);
        dots[i].setAttribute('cx', x(hovered)); dots[i].setAttribute('cy', y(row[key]));
      });
      guide.setAttribute('x1', x(hovered)); guide.setAttribute('x2', x(hovered)); marker.setAttribute('visibility', 'visible');
      tooltip.replaceChildren(...content); tooltip.hidden = false;
      tooltip.style.top = '8px';
      const anchor = x(hovered), available = chart.getBoundingClientRect().width;
      const preferred = anchor + 14 + tooltip.offsetWidth < available ? anchor + 14 : anchor - tooltip.offsetWidth - 14;
      tooltip.style.left = `${Math.max(0, Math.min(available - tooltip.offsetWidth, preferred))}px`;
    }
    function pointerYear(event) {const box = chart.getBoundingClientRect(); return Math.max(2025, Math.min(2085, 2025 + Math.round(((event.clientX - box.left) / box.width * width - left) / (right - left) * 60)));}
    function hide() {tooltip.hidden = true; marker.setAttribute('visibility', 'hidden');}
    target.addEventListener('pointermove', event => inspect(pointerYear(event)));
    target.addEventListener('pointerleave', hide);
    target.addEventListener('click', event => {selectYear(pointerYear(event)); inspect(year);});
    target.addEventListener('focus', () => inspect(year)); target.addEventListener('blur', hide);
    target.addEventListener('keydown', event => {
      const next = {ArrowLeft:year-1, ArrowRight:year+1, Home:2025, End:2085}[event.key];
      if (next !== undefined) {event.preventDefault(); selectYear(next); inspect(year);} else if (event.key === 'Escape') hide();
    });
    drawing.append(chartCursor, marker, target); chart.replaceChildren(drawing);
    $('bureauChartTitle').textContent = spec.title; $('bureauChartUnit').textContent = spec.unit;
    const legend = document.createDocumentFragment();
    for (const [, label, color] of spec.series) {const entry = node('span'), swatch = node('i'); swatch.style.background = color; entry.append(swatch, document.createTextNode(label)); legend.append(entry);}
    $('bureauLegend').replaceChildren(legend);
    for (const button of $('bureauChartTabs').children) {const active = button.dataset.view === view; button.setAttribute('aria-selected', String(active)); button.tabIndex = active ? 0 : -1; if (active) $('bureauChartPanel').setAttribute('aria-labelledby', button.id);}
  }
  function renderAll() {
    const p = data.profile;
    $('bureauResults').hidden = false;
    $('bureauTitle').textContent = `${p.name}铁路分局 · 六十年经营试算`;
    const region = catalog.regions.find(r => r.id === p.region_id);
    $('bureauSubtitle').textContent = `${region.name}经济区 · ${p.type} · 金额按 2025 年不变购买力计算`;
    $('bureauScenario').textContent = `情景倾向：${data.scenario.name}`;
    const years = data.rows.slice(1);
    setSigned($('totalSurplus'), years.reduce((sum, r) => sum + r.operating_surplus_yi, 0));
    $('lossYears').textContent = `亿元 · 2026—2085，${years.filter(r => r.operating_surplus_yi < 0).length} 年亏损`;
    const annual = document.createDocumentFragment();
    for (const row of data.rows) {
      const tr = node('tr'); tr.dataset.year = row.year;
      const first = node('th'); first.scope = 'row'; const button = node('button', row.year); button.type = 'button'; button.dataset.year = row.year; button.setAttribute('aria-label', `查看 ${row.year} 年明细`); first.append(button); tr.append(first);
      for (const [key] of annualColumns.slice(1)) {const cell = node('td', fixed(row[key])); if (key === 'operating_surplus_yi') cell.className = signClass(row[key]); tr.append(cell);}
      annual.append(tr);
    }
    $('annualRows').replaceChildren(annual);
    const config = document.createDocumentFragment();
    for (const [s, name] of segments) for (const [kind, label] of inputs) {
      const c = p.cost_inputs[s][kind], tr = node('tr');
      for (const value of [`${name} / ${label}`, fixed(c.base_cost_yi, 3), `${fixed(c.fixed_share*100, 1)}%`, `${fixed((1-c.fixed_share)*100, 1)}%`, `${fixed(c.variable_passenger_share*100, 1)}%`, `${fixed(c.passenger_congestion)} / ${fixed(c.freight_congestion)}`, kind==='wage'?fixed(c.labor_adjustment_theta):'—']) tr.append(node('td', value));
      config.append(tr);
    }
    $('configRows').replaceChildren(config);
    $('configReference').textContent = `客运基准 ${fixed(p.transport.base_passenger_trips_10k)} 万人次；货运基准 ${fixed(p.transport.base_freight_tons_10k)} 万吨。基期单位净收入：客运 ${fixed(p.finance_base_yi.passenger_revenue*10000/p.transport.base_passenger_trips_10k)} 元／人次、货运 ${fixed(p.finance_base_yi.freight_revenue*10000/p.transport.base_freight_tons_10k)} 元／吨。站务收入的客运关联权重 ${fixed(p.station_revenue_passenger_share*100, 0)}%。普通货运单位收益系数为货运量倍数的0.15次方（0.85—1.15），站务两项各为对应运量倍数的0.10次方（0.90—1.10）。客运票务收益不变。`;
    $('bureauVersion').textContent = `${data.modelVersion} · 宏观 V0.5 · 配置 ${data.bureauConfigHash.slice(0, 10)} · Seed ${data.seed}`;
    const audit = data.calibrationAudit;
    const linearReference = !['northeast', 'north'].includes(p.region_id);
    const regionBaseNet = audit?.bureaus.reduce((sum, b) => sum + b.base_net_yi, 0) || 0;
    $('calibrationTitle').textContent = `${region.name} · 96 个 Seed 经营对照`;
    $('referenceLossHead').textContent = linearReference ? '线性参考亏损占比' : '原亏损占比';
    $('referenceSurplusHead').textContent = linearReference ? '线性参考结余' : '原结余中位数';
    $('calibrationScopeNote').textContent = `同一组 Seed 0—95、客货运和成本路径。地区金额先逐 Seed 加总再取中位数；亏损样本占比按“分局×Seed”统计。累计为2026—2085年。${linearReference ? `线性参考使用相同${region.name}基期参数，仅关闭收益弹性，并非历史旧模型。${region.name}净结算各家独立，基期合计${fixed(regionBaseNet)}亿元。` : '东北独立新增收入，华北保持90%原基值。'}不设跨区域资金池。`;
    const modeRows = document.createDocumentFragment(), bureauRows = document.createDocumentFragment(), scenarioRows = document.createDocumentFragment();
    if (audit) {
      $('calibrationNote').textContent = `Seed ${audit.seedRange[0]}—${audit.seedRange[1]}，共 ${audit.seedCount} 个。地区统计与上方所选 Seed 无关。当前收益弹性：普通货运0.15、站务0.10；净结算使用货运收益系数。`;
      for (const [key, label] of Object.entries(audit.modes)) {
        const r = audit.region[key], tr = node('tr');
        if (key === 'combined_v04') tr.className = 'current-bureau';
        const th = node('th', label); th.scope = 'row'; tr.append(th);
        tr.append(node('td', fixed(r.end_surplus_median_yi)), node('td', `${fixed(r.pooled_end_loss_fraction*100,1)}%`), node('td', fixed(r.cumulative_surplus_median_yi)));
        modeRows.append(tr);
      }
      for (const group of Object.values(audit.scenarioGroups || {})) {
        const tr = node('tr'), th = node('th',group.name); th.scope='row'; tr.append(th);
        tr.append(node('td',String(group.seedCount)),node('td',fixed(group.end_total_surplus_median_yi)),node('td',`${fixed(group.pooled_end_loss_fraction*100,1)}%`));
        scenarioRows.append(tr);
      }
      for (const b of audit.bureaus) {
        const a = b.scenarios.legacy_v03, c = b.scenarios.combined_v04, tr = node('tr');
        if (b.bureau_id === p.bureau_id) tr.className = 'current-bureau';
        const th = node('th', b.name); th.scope = 'row'; tr.append(th);
        tr.append(node('td', `${fixed(a.end_loss_fraction*100,1)}%`), node('td', `${fixed(c.end_loss_fraction*100,1)}%`), node('td', fixed(a.end_surplus_median_yi)), node('td', fixed(c.end_surplus_median_yi)), node('td', fixed(b.base_net_yi)));
        bureauRows.append(tr);
      }
    } else $('calibrationNote').textContent = '当前配置尚无匹配的96 Seed报告，请重跑V0.4审计并重启服务。';
    $('calibrationModes').replaceChildren(modeRows);
    $('calibrationScenarios').replaceChildren(scenarioRows);
    $('calibrationRows').replaceChildren(bureauRows);
    renderCash();
    renderValuation();
    drawChart(); renderYear();
  }
  async function getJSON(url) {
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 20000);
    try {const response = await fetch(url, {cache:'no-store', signal:controller.signal}); if (!response.ok) throw new Error(`请求失败（${response.status}）`); return await response.json();}
    finally {clearTimeout(timeout);}
  }
  async function load(seed, bureau) {
    if (busy) return;
    disable(true); status(`正在生成 Seed ${seed} 的六十年经营情景…`);
    try {
      const key = `${seed}|${bureau}`;
      const next = cache.get(key) || await getJSON(`./api/bureau?seed=${seed}&bureau=${encodeURIComponent(bureau)}`);
      if (next.seed !== seed || next.profile?.bureau_id !== bureau || next.baseYear !== 2025 || next.rows?.length !== 61 || next.rows.some((r, i) => r.year !== 2025 + i || !Number.isFinite(r.cost_yi) || !Number.isFinite(r.operating_surplus_yi))) throw new Error('返回的分局数据不完整');
      if (next.cash?.modelVersion !== 'railway-bureau-annual-cash-dividends-v0.3' || next.cash.rows?.length !== 61 || next.cash.rows.some((r,i)=>r.year!==2025+i || r.bureau_id!==bureau || !Number.isFinite(r.cash_closing_yi) || !Number.isFinite(r.cash_carryover_yi) || !Number.isFinite(r.cash_opening_yi) || !Number.isFinite(r.cash_dividend_yi) || !Number.isFinite(r.cash_without_dividends_closing_yi) || (i>0 && r.cash_funding_year!==r.year-1))) throw new Error('现金数据不完整，请更新本地服务。');
      const cashByYear=new Map(next.cash.rows.map(r=>[r.year,r]));
      if(next.officialValuation?.modelVersion!=='railway-official-valuation-v0.1' || next.officialValuation.rows?.length!==61 || next.officialValuation.rows.some((r,i)=>r.year!==2025+i || r.bureau_id!==bureau || !Number.isFinite(r.valuation_official_yi) || r.forecastRows?.length!==10)) throw new Error('国铁估值数据不完整，请更新本地服务。');
      const valuationByYear=new Map(next.officialValuation.rows.map(r=>[r.year,r]));
      next.rows=next.rows.map(r=>({...r,...cashByYear.get(r.year),...valuationByYear.get(r.year)}));
      data = next; cache.set(key, next); if (cache.size > 4) cache.delete(cache.keys().next().value);
      $('bureauRegion').value = data.profile.region_id; populateBureaus(bureau); $('bureauSeed').value = String(seed);
      renderAll();
      status(`当前 Seed ${seed} · 已生成 61 个年度数据点。已接入 ${new Set(catalog.bureaus.map(b => b.region_id)).size} 个经济区，共 ${catalog.bureaus.length} 家分局。`);
    } catch (error) {
      status(`试算加载失败。请确认本地 serve.py 服务已更新并重试。${data ? '当前保留上一份结果。' : ''} ${error.name === 'AbortError' ? '请求超时。' : error.message}`, true);
      if (data) {$('bureauRegion').value = data.profile.region_id; populateBureaus(data.profile.bureau_id); $('bureauSeed').value = String(data.seed);}
    } finally {disable(false);}
  }
  function submit() {try {load(seedValue(), $('bureauSelect').value);} catch (error) {status(error.message, true);}}
  $('bureauForm').addEventListener('submit', event => {event.preventDefault(); if (!catalog) {initialize(); return;} submit();});
  $('bureauSelect').addEventListener('change', submit);
  $('bureauRegion').addEventListener('change', () => {populateBureaus(); submit();});
  $('bureauYear').addEventListener('input', () => selectYear(Number($('bureauYear').value)));
  $('annualRows').addEventListener('click', event => {const button = event.target.closest('button[data-year]'); if (button) selectYear(Number(button.dataset.year));});
  $('cashLedgerRows').addEventListener('click', event => {const button=event.target.closest('button[data-year]'); if(button) selectYear(Number(button.dataset.year));});
  $('valuationAnnualRows').addEventListener('click',event=>{const b=event.target.closest('button[data-year]');if(b)selectYear(Number(b.dataset.year));});
  $('bureauChartTabs').addEventListener('click', event => {const button = event.target.closest('button[data-view]'); if (!button || !data) return; view = button.dataset.view; syncView(); drawChart(); syncLocation();});
  $('bureauChartTabs').addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault(); const buttons = [...$('bureauChartTabs').children], i = buttons.findIndex(b => b.dataset.view === view);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length-1 : (i + (event.key === 'ArrowLeft' ? -1 : 1) + buttons.length) % buttons.length;
    buttons[next].click(); buttons[next].focus();
  });
  $('randomBureau').addEventListener('click', () => {
    if (!catalog || busy) return;
    const bits = crypto.getRandomValues(new Uint32Array(2)); let seed = (bits[0] & 0x1fffff) * 4294967296 + bits[1];
    if (seed === data?.seed) seed = seed === Number.MAX_SAFE_INTEGER ? 0 : seed + 1;
    $('bureauSeed').value = String(seed); submit();
  });
  function exportCSV() {
    if (!data) return;
    const columns = [['seed', 'Seed'], ['bureau_name', '铁路分局'], ['model_version', '经营模型版本'], ['bureau_config_hash', '经营配置哈希'], ...annualColumns,
      ['passenger_index', '客运量指数'], ['freight_index', '货运量指数'], ...inputs.map(([k, n]) => [k+'_cost_yi', n+'成本']), ['fixed_operating_cost_yi', '固定成本合计'], ['volume_operating_cost_yi', '变动成本合计'],
      ['regional_wage_index','地区实际工资指数'],['historical_wage_peak_index','历史工资高点指数'],['v02_wage_cost_yi','A原V0.2人工成本'],['full_wage_cost_yi','B工资完全传导人工成本'],['v02_operating_surplus_yi','A原V0.2经营结余'],['full_operating_surplus_yi','B工资完全传导经营结余'],['core_operating_surplus_yi','不含隐藏净结算的经营结余'],['unscaled_hidden_freight_income_yi','本局基值100%权重净结算收入'],['settlement_base_net_yi','本局生效基期净结算'],['freight_unit_yield_factor','普通货运单位收益系数'],['station_passenger_unit_yield_factor','站务客运单位收益系数'],['station_freight_unit_yield_factor','站务货运单位收益系数'],['settlement_unit_yield_factor','净结算单位收益系数']];
    for (const [s, name] of segments) for (const [k, label] of inputs) for (const [field, title] of [['fixed_cost_yi', '固定支出'], ['variable_cost_yi', '变动支出'], ['cost_yi', '合计'], ['price_factor', '价格倍数'], ['unit_cost_factor','综合投入系数'], ['workload_factor', '工作量倍数']]) columns.push([`${s}.${k}.${field}`, `${name}/${label}/${title}`]);
    if (view==='cash' || view==='cash_compare') columns.splice(0,columns.length,['seed','Seed'],['bureau_name','铁路分局'],...cashColumns);
    else if(view==='valuation') columns.splice(0,columns.length,['seed','Seed'],['bureau_name','铁路分局'],...valuationColumns,['valuation_discount_rate_pct','折现率（%）'],['valuation_next_surplus_forecast_yi','下一年经营结余预测'],['valuation_cash_cover_months','融资前预测储备月数'],['valuation_active_band','增资档位'],['valuation_issue_multiplier','增资定价倍数'],['valuation_tail_years','末年延续年数']);
    else columns.push(...cashColumns.slice(1));
    columns.push(['cash_profit_dividend_yi','利润分红'],['cash_excess_dividend_yi','超额现金分红'],['cash_without_dividends_closing_yi','不分红参考现金'],['cash_without_dividends_cumulative_equity_yi','不分红参考累计增资'],['cash_dividend_status','分红状态'],['cash_dividend_minimum_yi','分红最低保留现金'],['cash_dividend_comfortable_yi','充裕现金线']);
    columns.push(['cash_model_version','现金模型版本'],['cash_config_hash','现金配置哈希']);
    columns.push(['valuation_model_version','估值模型版本'],['valuation_config_hash','估值配置哈希']);
    const quote = value => `"${String(value).replaceAll('"', '""')}"`;
    const lines = [columns.map(([, title]) => quote(title)).join(',')];
    for (const row of data.rows) lines.push(columns.map(([key]) => {
      let value;
      if (key === 'bureau_config_hash') value = data.bureauConfigHash;
      else if (key === 'cash_config_hash') value = data.cash.configHash;
      else if (key === 'cash_model_version') value = data.cash.modelVersion;
      else if (key === 'valuation_model_version') value = data.officialValuation.modelVersion;
      else if (key === 'valuation_config_hash') value = data.officialValuation.configHash;
      else if (key.includes('.')) {const [s, k, field] = key.split('.'); value = row.cost_breakdown[s][k][field];}
      else value = row[key];
      return quote(value ?? '');
    }).join(','));
    const url = URL.createObjectURL(new Blob(['\ufeff', lines.join('\r\n')], {type:'text/csv;charset=utf-8'}));
    const link = node('a'); link.href = url; link.download = `${data.profile.bureau_id}-seed-${data.seed}-${view==='valuation'?'valuation-':view==='cash'||view==='cash_compare'?'cash-':''}2025-2085.csv`; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  $('exportBureau').addEventListener('click',exportCSV);
  $('exportCash').addEventListener('click',exportCSV);
  $('exportValuation').addEventListener('click',exportCSV);
  let previousWidth = 0;
  new ResizeObserver(entries => {const width = Math.round(entries[0].contentRect.width); if (width !== previousWidth) {previousWidth = width; drawChart();}}).observe($('bureauChart').parentElement);
  async function initialize() {
    disable(true);
    try {
      catalog = await getJSON('./api/bureau-catalog');
      if (!catalog.regions?.length || !catalog.bureaus?.length) throw new Error('未读取到分局配置');
      $('bureauRegion').replaceChildren(...catalog.regions.map(r => {const count = catalog.bureaus.filter(b => b.region_id === r.id).length, option = node('option', `${r.name}${count ? ` · ${count} 家` : ' · 待初始化'}`); option.value = r.id; option.disabled = !count; return option;}));
      const requestedBureau = query.get('bureau') || query.get('division');
      const chosen = catalog.bureaus.find(b => b.bureau_id === requestedBureau);
      const region = chosen?.region_id || query.get('region') || 'northeast';
      $('bureauRegion').value = catalog.bureaus.some(b => b.region_id === region) ? region : 'northeast';
      populateBureaus(chosen?.bureau_id || 'jiamusi');
      $('bureauSeed').value = query.get('seed') || '20261014';
      disable(false); submit();
    } catch (error) {disable(false); status(`未能读取配置，请确认本地服务已更新，点击“生成试算”重试。${error.message}`, true);}
  }
  initialize();
})();
