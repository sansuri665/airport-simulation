    function fmtPct(value, digits = 2) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      const sign = value > 0 ? "+" : "";
      return `${sign}${value.toFixed(digits)}%`;
    }

    function fmtPp(value, digits = 2) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      const sign = value > 0 ? "+" : "";
      return `${sign}${value.toFixed(digits)}pp`;
    }

    function fmtLevelPct(value, digits = 2) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      return `${value.toFixed(digits)}%`;
    }

    function hasInflation(row) {
      return typeof row?.headline_inflation_pct === "number" && !Number.isNaN(row.headline_inflation_pct);
    }

    function hasPolicy(row) {
      return typeof row?.global_policy_rate_pct === "number" && !Number.isNaN(row.global_policy_rate_pct);
    }

    function hasYield(row) {
      return typeof row?.global_10y_yield_pct === "number" && !Number.isNaN(row.global_10y_yield_pct);
    }

    function hasDollar(row) {
      return typeof row?.global_dollar_index === "number" && !Number.isNaN(row.global_dollar_index);
    }

    function hasCredit(row) {
      return typeof row?.global_high_yield_spread_bps === "number" && !Number.isNaN(row.global_high_yield_spread_bps);
    }

    function hasAsset(row) {
      return typeof row?.global_equity_price_index === "number" && !Number.isNaN(row.global_equity_price_index);
    }

    function hasOil(row) {
      return typeof row?.brent_oil_price_usd === "number" && !Number.isNaN(row.brent_oil_price_usd);
    }

    function hasFeedback(row) {
      return typeof row?.macro_feedback_intensity_index === "number" && !Number.isNaN(row.macro_feedback_intensity_index);
    }

    function fmtUsd(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      return `$${value.toFixed(1)}T`;
    }

    function fmtGdp(value, row) {
      if (row?.display_gdp_unit === "index") return fmtIndex(value);
      return fmtUsd(value);
    }

    function fmtIndex(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      return value.toFixed(1);
    }

    function fmtBps(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      return `${value.toFixed(0)}bps`;
    }

    function fmtOil(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "-";
      return `$${value.toFixed(1)}`;
    }

    function fmtOilMetric(row) {
      if (row?.oil_display_unit === "index") return fmtIndex(row.brent_oil_price_usd);
      return fmtOil(row?.brent_oil_price_usd);
    }

    function toneForRegime(regime) {
      if (String(regime || "").includes("crisis") || String(regime || "").includes("recession") || String(regime || "").includes("credit_tightening")) return "bad";
      if (String(regime || "").includes("stagflation")) return "hot";
      if (String(regime || "").includes("soft_landing") || String(regime || "").includes("wealth_led")) return "good";
      if (["crisis_onset", "deep_crisis", "recession", "stress_slowdown"].includes(regime)) return "bad";
      if (["overheating_boom", "high_expansion"].includes(regime)) return "hot";
      if (["crisis_repair", "recovery", "normal_expansion"].includes(regime)) return "good";
      return "neutral";
    }

    function growthClass(value) {
      if (value > 0) return "positive";
      if (value < 0) return "negative";
      return "";
    }
