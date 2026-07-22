(function exposeFinancingRate(root) {
  "use strict";

  function finiteOrNull(value) {
    if (value === null || value === undefined || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function finiteBenchmark(value) {
    if (value === null || value === undefined || value === "") {
      return { value: null, reason: "missing_value" };
    }
    const number = Number(value);
    if (Number.isNaN(number)) return { value: null, reason: "invalid_value" };
    if (!Number.isFinite(number)) return { value: null, reason: "non_finite_value" };
    return { value: number, reason: "" };
  }

  function policyNumber(policy, key, fallback) {
    const value = finiteOrNull(policy?.[key]);
    return value === null ? fallback : value;
  }

  function interpolateLeverageSpread(model, leveragePct) {
    if (!model?.enabled) return 0;
    const curve = (model.spread_curve || [])
      .map((point) => [Number(point.liability_ratio_pct), Number(point.additional_spread_bps)])
      .filter((point) => Number.isFinite(point[0]) && Number.isFinite(point[1]))
      .sort((left, right) => left[0] - right[0]);
    if (!curve.length) return 0;
    if (leveragePct <= curve[0][0]) return curve[0][1];
    for (let index = 1; index < curve.length; index += 1) {
      const [leftRatio, leftSpread] = curve[index - 1];
      const [rightRatio, rightSpread] = curve[index];
      if (leveragePct <= rightRatio) {
        if (rightRatio <= leftRatio) return rightSpread;
        const weight = (leveragePct - leftRatio) / (rightRatio - leftRatio);
        return leftSpread + (rightSpread - leftSpread) * weight;
      }
    }
    return curve[curve.length - 1][1];
  }

  function buildLoanRateQuote({ product, policy, finance, principalMillion, tenor, grace }) {
    const loanType = String(product?.loan_type || "long_term");
    const isShort = loanType === "short_term";
    const benchmarkType = isShort ? "policy_rate" : "ten_year_yield";
    const benchmark = finiteBenchmark(
      isShort ? finance?.macroPolicyRatePct : finance?.macroTenYearYieldPct,
    );
    const reportedSource = String(
      (isShort ? finance?.macroPolicyRateSource : finance?.macroTenYearYieldSource) || "",
    );
    const fallbackKey = isShort
      ? "fallback_short_term_rate_pct"
      : "fallback_long_term_rate_pct";
    let benchmarkFallbackReason = benchmark.reason;
    if (!benchmarkFallbackReason && reportedSource !== "regional_macro_annual") {
      benchmarkFallbackReason = "source_mismatch";
    }
    const benchmarkFallbackUsed = Boolean(benchmarkFallbackReason);
    const benchmarkRate = benchmarkFallbackUsed
      ? policyNumber(policy, fallbackKey, isShort ? 3.6 : 4.8)
      : benchmark.value;
    const benchmarkSource = benchmarkFallbackUsed ? fallbackKey : reportedSource;

    const referenceAdjustmentBps = policyNumber(
      policy,
      `${loanType}_reference_adjustment_pct`,
      0,
    ) * 100;
    const productTypeSpreadBps = policyNumber(policy, `${loanType}_spread_bps`, 0);
    const productSpreadBps = referenceAdjustmentBps + productTypeSpreadBps;
    const termSpreadBps = policyNumber(product?.tenor_spread_bps || {}, tenor, 0);
    const graceSpreadBps = policyNumber(product?.grace_spread_bps || {}, grace, 0);
    const termAndGraceSpreadBps = termSpreadBps + graceSpreadBps;

    const hyBaseline = policyNumber(policy, "hy_spread_baseline_bps", 420);
    const hySpread = finiteOrNull(finance?.macroHySpreadBps);
    const effectiveHySpread = hySpread === null ? hyBaseline : hySpread;
    const hyCapture = policyNumber(policy, "hy_spread_capture_ratio", 0);
    const hyCreditSpreadBps = Math.max(0, effectiveHySpread - hyBaseline) * hyCapture;
    const cityCreditSpreadBps = policyNumber(policy, "city_risk_spread_bps", 0);
    const creditSpreadBps = hyCreditSpreadBps + cityCreditSpreadBps;

    const assets = finiteOrNull(finance?.totalAssets) ?? 0;
    const liabilities = finiteOrNull(finance?.totalLiabilities) ?? 0;
    const principal = finiteOrNull(principalMillion) ?? 0;
    const beforeLeverage = assets > 0 ? liabilities / assets * 100 : 0;
    const postLeverage = assets + principal > 0
      ? (liabilities + principal) / (assets + principal) * 100
      : 0;
    const leverageModel = policy?.leverage_spread_model || {};
    const leverageSpreadBps = interpolateLeverageSpread(leverageModel, postLeverage);
    const beforeLimit = policyNumber(
      leverageModel,
      "block_if_begin_ratio_at_or_above_pct",
      80,
    );
    const afterLimit = policyNumber(
      leverageModel,
      "block_if_post_draw_ratio_at_or_above_pct",
      80,
    );
    const blocked = beforeLeverage >= beforeLimit || postLeverage >= afterLimit;
    const blockReason = beforeLeverage >= beforeLimit
      ? "begin_leverage_limit"
      : (postLeverage >= afterLimit ? "post_draw_leverage_limit" : "");

    const unclampedRate = benchmarkRate
      + productSpreadBps / 100
      + termAndGraceSpreadBps / 100
      + creditSpreadBps / 100
      + leverageSpreadBps / 100;
    const minimum = policyNumber(policy, "min_annual_interest_rate_pct", 1);
    const maximum = policyNumber(policy, "max_annual_interest_rate_pct", 9.5);
    const annualRate = Math.max(minimum, Math.min(maximum, unclampedRate));

    return {
      loan_type: loanType,
      benchmark_type: benchmarkType,
      benchmark_source: benchmarkSource,
      benchmark_rate_pct: benchmarkRate,
      benchmark_fallback_used: benchmarkFallbackUsed,
      benchmark_fallback_reason: benchmarkFallbackReason,
      product_reference_adjustment_bps: referenceAdjustmentBps,
      product_type_spread_bps: productTypeSpreadBps,
      product_spread_bps: productSpreadBps,
      term_spread_bps: termSpreadBps,
      grace_spread_bps: graceSpreadBps,
      term_and_grace_spread_bps: termAndGraceSpreadBps,
      hy_credit_spread_bps: hyCreditSpreadBps,
      city_credit_spread_bps: cityCreditSpreadBps,
      credit_spread_bps: creditSpreadBps,
      leverage_spread_bps: leverageSpreadBps,
      unclamped_annual_rate_pct: unclampedRate,
      annual_rate_pct: annualRate,
      rate_floor_applied: unclampedRate < minimum,
      rate_cap_applied: unclampedRate > maximum,
      rate_model_version: String(policy?.model_version || "general-loan-rate-v0.3"),
      before_draw_liability_ratio_pct: beforeLeverage,
      post_draw_liability_ratio_pct: postLeverage,
      blocked,
      block_reason: blockReason,
    };
  }

  root.AirportFinancingRate = Object.freeze({
    buildLoanRateQuote,
    interpolateLeverageSpread,
  });
})(typeof window === "undefined" ? globalThis : window);
