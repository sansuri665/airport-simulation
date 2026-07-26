window.AirportGlobalScenarioModel = (() => {
    function clamp(value, low, high) {
      return Math.max(low, Math.min(high, value));
    }

    function smooth(oldValue, target, speed) {
      return oldValue * (1 - speed) + target * speed;
    }

    function pctChange(current, previous) {
      if (previous <= 0) return 0;
      return (current / previous - 1) * 100;
    }

    function compoundIndexWithSoftDrag(previous, totalReturnPct, floor, softStart, softness = 0.65) {
      let adjustedReturn = totalReturnPct;
      if (totalReturnPct > 0 && previous > softStart) {
        adjustedReturn *= Math.pow(softStart / previous, softness);
      }
      return Math.max(floor, previous * (1 + adjustedReturn / 100));
    }

    function piecewiseCreditConvexityPressure(hySpread) {
      return clamp(
        0.030 * Math.max(0, Math.min(hySpread, 800) - 500)
        + 0.075 * Math.max(0, Math.min(hySpread, 1200) - 800)
        + 0.120 * Math.max(0, hySpread - 1200),
        0,
        100,
      );
    }

    function piecewiseCreditGdpDrag(hySpread) {
      return (
        -0.0022 * Math.max(0, Math.min(hySpread, 800) - 500)
        - 0.0050 * Math.max(0, Math.min(hySpread, 1200) - 800)
        - 0.0070 * Math.max(0, hySpread - 1200)
      );
    }

    function sinWave(t, period, phase) {
      return Math.sin(2 * Math.PI * (t / period) + phase);
    }

    function makeRng(seed) {
      let stateValue = seed >>> 0;
      let spare = null;
      return {
        random() {
          stateValue += 0x6D2B79F5;
          let t = stateValue;
          t = Math.imul(t ^ (t >>> 15), t | 1);
          t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
          return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        },
        uniform(low, high) {
          return low + (high - low) * this.random();
        },
        randint(low, high) {
          return Math.floor(this.uniform(low, high + 1));
        },
        gauss(mean, sigma) {
          if (spare !== null) {
            const value = spare;
            spare = null;
            return mean + sigma * value;
          }
          const u = Math.max(1e-12, this.random());
          const v = Math.max(1e-12, this.random());
          const radius = Math.sqrt(-2 * Math.log(u));
          const theta = 2 * Math.PI * v;
          spare = radius * Math.sin(theta);
          return mean + sigma * radius * Math.cos(theta);
        },
      };
    }

    function dynamicParams() {
      const baseRows = state.rows.filter((row) => row.seed === state.seed).sort((a, b) => a.year - b.year);
      return {
        years: Math.max(1, baseRows.length - 1) || 60,
        startYear: baseRows[0]?.year ?? 2025,
        initialGdp: baseRows[0]?.global_gdp_trillion_usd ?? 110,
        initialIndex: 100,
        baseTrendGrowth: 2.75,
        terminalTrendGrowth: 1.75,
        trendSlowdownHalfLife: 70,
        trendNoise: 0.16,
        volatilityScale: 1.55,
        outputGapPersistence: 0.68,
        outputGapAdjustmentSpeed: 0.34,
        outputGapCycleLoading: 0.56,
        outputGapShockLoading: 0.92,
        outputGapCap: 13.5,
        growthAdjustmentSpeed: 0.50,
        maxGrowthStep: 2.05,
        shockDecay: 0.52,
        shockReleaseSpeed: 0.50,
        directCycleGrowthLoading: 0.10,
        directShockGrowthLoading: 0.52,
        financialStressDecay: 0.62,
        crisisEraChance: 0.042,
        crisisCycleSensitivity: 0.010,
        crisisMinDuration: 3,
        crisisMaxDuration: 7,
        crisisSeverityMin: 0.55,
        crisisSeverityMax: 1.00,
        crisisCooldownMin: 4,
        crisisCooldownMax: 8,
        crisisChance: 0.018,
        deepCrisisChance: 0.006,
        boomChance: 0.060,
        maxPositiveGrowth: 9.5,
        maxNegativeGrowth: -8.5,
      };
    }

    function drawCycleSpecs(rng, volatilityScale) {
      return {
        inventory: {
          name: "inventory",
          period: rng.uniform(3.2, 5.2),
          amplitude: rng.uniform(0.25, 0.65) * volatilityScale,
          phase: rng.uniform(0, 2 * Math.PI),
          persistence: rng.uniform(0.25, 0.45),
          noise: 0.10 * volatilityScale,
        },
        investment: {
          name: "investment",
          period: rng.uniform(7.0, 11.5),
          amplitude: rng.uniform(0.65, 1.35) * volatilityScale,
          phase: rng.uniform(0, 2 * Math.PI),
          persistence: rng.uniform(0.35, 0.58),
          noise: 0.12 * volatilityScale,
        },
        infrastructure: {
          name: "infrastructure",
          period: rng.uniform(16.0, 25.0),
          amplitude: rng.uniform(0.35, 0.95) * volatilityScale,
          phase: rng.uniform(0, 2 * Math.PI),
          persistence: rng.uniform(0.45, 0.70),
          noise: 0.08 * volatilityScale,
        },
        longWave: {
          name: "long_wave",
          period: rng.uniform(48.0, 68.0),
          amplitude: rng.uniform(0.55, 1.15) * volatilityScale,
          phase: rng.uniform(0, 2 * Math.PI),
          persistence: rng.uniform(0.55, 0.80),
          noise: 0.05 * volatilityScale,
        },
      };
    }

    function cycleComponent(t, spec, simState, rng) {
      const raw = spec.amplitude * sinWave(t, spec.period, spec.phase) + rng.gauss(0, spec.noise);
      const previous = simState.cycleMemory[spec.name] ?? 0;
      const value = smooth(raw, previous, spec.persistence);
      simState.cycleMemory[spec.name] = value;
      return value;
    }

    function longRunTrend(t, params, rng) {
      const slowdownWeight = 1 - Math.exp(-t / Math.max(1, params.trendSlowdownHalfLife));
      const deterministic = params.baseTrendGrowth * (1 - slowdownWeight) + params.terminalTrendGrowth * slowdownWeight;
      return deterministic + rng.gauss(0, params.trendNoise * params.volatilityScale);
    }

    function crisisPhase(progress) {
      if (progress < 0.26) return "crisis_onset";
      if (progress < 0.58) return "deep_crisis";
      return "crisis_repair";
    }

    function maybeStartCrisisEra(simState, params, rng, cycleGrowth) {
      if (simState.crisisYearsLeft > 0 || simState.crisisCooldownYears > 0) return;
      const chance = params.crisisEraChance + Math.max(0, -cycleGrowth) * params.crisisCycleSensitivity;
      if (rng.random() >= chance) return;
      simState.crisisTotalYears = rng.randint(params.crisisMinDuration, params.crisisMaxDuration);
      simState.crisisYearsLeft = simState.crisisTotalYears;
      simState.crisisAge = 0;
      simState.crisisSeverity = rng.uniform(params.crisisSeverityMin, params.crisisSeverityMax);
    }

    function drawEventShock(simState, params, rng, cycleGrowth) {
      let shock = 0;
      let crisisIntensity = 0;
      let boomIntensity = 0;
      let phase = "";
      maybeStartCrisisEra(simState, params, rng, cycleGrowth);

      if (simState.crisisYearsLeft > 0) {
        const progress = simState.crisisAge / Math.max(1, simState.crisisTotalYears - 1);
        let phaseLoad = 0;
        phase = crisisPhase(progress);
        if (phase === "crisis_onset") {
          phaseLoad = 0.45 + progress / 0.26 * 0.35;
          shock = -(0.95 + 2.15 * phaseLoad) * params.volatilityScale;
        } else if (phase === "deep_crisis") {
          phaseLoad = 0.85 + 0.15 * Math.sin(Math.PI * (progress - 0.26) / 0.32);
          shock = -(1.45 + 2.95 * phaseLoad) * params.volatilityScale;
        } else {
          const repairLeft = Math.max(0, (1 - progress) / 0.42);
          phaseLoad = 0.20 + 0.65 * repairLeft;
          shock = -(0.25 + 1.35 * phaseLoad) * params.volatilityScale;
          boomIntensity = clamp(0.25 * (1 - repairLeft), 0, 0.35);
        }
        crisisIntensity = clamp(phaseLoad * simState.crisisSeverity, 0, 1);
        shock *= 0.72 + 0.55 * simState.crisisSeverity;
        simState.crisisAge += 1;
        simState.crisisYearsLeft -= 1;
        if (simState.crisisYearsLeft <= 0) {
          simState.crisisTotalYears = 0;
          simState.crisisAge = 0;
          simState.crisisSeverity = 0;
          simState.crisisCooldownYears = rng.randint(params.crisisCooldownMin, params.crisisCooldownMax);
        }
        return { shock, crisisIntensity, boomIntensity, phase };
      }

      if (simState.crisisCooldownYears > 0) simState.crisisCooldownYears -= 1;
      if (rng.random() < params.deepCrisisChance) {
        crisisIntensity = rng.uniform(0.70, 1.00);
        shock -= rng.uniform(3.5, 7.5) * params.volatilityScale * crisisIntensity;
        phase = "deep_crisis";
      } else if (rng.random() < params.crisisChance) {
        crisisIntensity = rng.uniform(0.25, 0.75);
        shock -= rng.uniform(1.0, 3.5) * params.volatilityScale * crisisIntensity;
        phase = "stress_slowdown";
      }
      if (rng.random() < params.boomChance && crisisIntensity < 0.20) {
        boomIntensity = rng.uniform(0.25, 1.00);
        shock += rng.uniform(0.8, 2.6) * params.volatilityScale * boomIntensity;
      }
      return { shock, crisisIntensity, boomIntensity, phase };
    }

    function classifyRegime(realizedGrowth, outputGap, stress, crisisIntensity, boomIntensity, phase) {
      if (phase === "crisis_onset") return "crisis_onset";
      if (phase === "deep_crisis") return "deep_crisis";
      if (phase === "crisis_repair") return realizedGrowth < 2.4 ? "crisis_repair" : "recovery";
      if (crisisIntensity >= 0.70 || realizedGrowth <= -2.0) return "deep_crisis";
      if (realizedGrowth < 0) return "recession";
      if (stress >= 65 && realizedGrowth < 1.2) return "stress_slowdown";
      if (outputGap <= -3 && realizedGrowth >= 2.0) return "recovery";
      if (boomIntensity >= 0.65 || (outputGap >= 4 && realizedGrowth >= 4)) return "overheating_boom";
      if (realizedGrowth >= 3.5) return "high_expansion";
      if (realizedGrowth <= 1.2) return "slowdown";
      return "normal_expansion";
    }

    function emptyMacroEventStub() {
      return {
        event_interface_version: "macro-event-interface-v0.1",
        event_type: "none",
        event_phase: "none",
        event_severity: 0,
        policy_rate_impulse: 0,
        liquidity_impulse: 0,
        credit_stress_impulse: 0,
        dollar_pressure_impulse: 0,
        energy_price_impulse: 0,
        gdp_lagged_support: 0,
      };
    }

    function buildMacroEventStub({ regime, phase, crisisIntensity, boomIntensity, shock, outputGap, stress }) {
      const severity = clamp(Math.max(
        crisisIntensity,
        boomIntensity * 0.70,
        Math.max(0, -shock) / 7,
        Math.max(0, stress - 35) / 60,
        Math.max(0, -outputGap) / 10,
      ), 0, 1);
      const stub = emptyMacroEventStub();

      if (regime === "crisis_onset") {
        return {
          ...stub,
          event_type: "financial_stress_event",
          event_phase: "onset",
          event_severity: severity,
          policy_rate_impulse: 0.10 * severity,
          liquidity_impulse: -0.25 * severity,
          credit_stress_impulse: 1.00 * severity,
          dollar_pressure_impulse: 0.35 * severity,
          energy_price_impulse: -0.25 * severity,
          gdp_lagged_support: -0.35 * severity,
        };
      }
      if (regime === "deep_crisis") {
        return {
          ...stub,
          event_type: "systemic_crisis",
          event_phase: "trough",
          event_severity: severity,
          policy_rate_impulse: -0.20 * severity,
          liquidity_impulse: 0.20 * severity,
          credit_stress_impulse: 1.20 * severity,
          dollar_pressure_impulse: 0.50 * severity,
          energy_price_impulse: -0.40 * severity,
          gdp_lagged_support: -0.55 * severity,
        };
      }
      if (["crisis_repair", "recovery"].includes(regime)) {
        return {
          ...stub,
          event_type: "central_bank_easing_placeholder",
          event_phase: "repair",
          event_severity: severity,
          policy_rate_impulse: -0.85 * severity,
          liquidity_impulse: 1.10 * severity,
          credit_stress_impulse: -0.70 * severity,
          dollar_pressure_impulse: -0.20 * severity,
          energy_price_impulse: 0.15 * severity,
          gdp_lagged_support: 0.45 * severity,
        };
      }
      if (regime === "stress_slowdown") {
        return {
          ...stub,
          event_type: "credit_stress_event",
          event_phase: phase || "slowdown",
          event_severity: severity,
          policy_rate_impulse: -0.25 * severity,
          liquidity_impulse: 0.30 * severity,
          credit_stress_impulse: 0.65 * severity,
          dollar_pressure_impulse: 0.20 * severity,
          energy_price_impulse: -0.10 * severity,
          gdp_lagged_support: -0.20 * severity,
        };
      }
      if (["high_expansion", "overheating_boom"].includes(regime)) {
        const hotSeverity = clamp(Math.max(boomIntensity, Math.max(0, outputGap) / 8), 0, 1);
        return {
          ...stub,
          event_type: "tightening_risk_placeholder",
          event_phase: "late_cycle",
          event_severity: hotSeverity,
          policy_rate_impulse: 0.45 * hotSeverity,
          liquidity_impulse: -0.35 * hotSeverity,
          credit_stress_impulse: 0.15 * hotSeverity,
          dollar_pressure_impulse: 0.10 * hotSeverity,
          energy_price_impulse: 0.25 * hotSeverity,
          gdp_lagged_support: -0.10 * hotSeverity,
        };
      }
      if (["recession", "slowdown"].includes(regime)) {
        return {
          ...stub,
          event_type: "demand_slowdown_event",
          event_phase: "slowdown",
          event_severity: severity,
          policy_rate_impulse: -0.15 * severity,
          liquidity_impulse: 0.15 * severity,
          credit_stress_impulse: 0.35 * severity,
          dollar_pressure_impulse: 0.10 * severity,
          energy_price_impulse: -0.15 * severity,
          gdp_lagged_support: -0.15 * severity,
        };
      }
      return stub;
    }

    function roundRow(row) {
      const rounded = { ...row };
      for (const key of numFields) {
        if (typeof rounded[key] === "number") rounded[key] = Number(rounded[key].toFixed(4));
      }
      return rounded;
    }

    function simulateDynamicGlobalGdp(seed, feedbackByIndex = {}) {
      const params = dynamicParams();
      const rng = makeRng(seed);
      const specs = drawCycleSpecs(rng, params.volatilityScale);
      const simState = {
        potentialIndex: params.initialIndex,
        realIndex: params.initialIndex,
        outputGap: rng.uniform(-1.2, 1.2),
        financialStress: rng.uniform(8, 22),
        shockStock: 0,
        lastGrowth: params.baseTrendGrowth,
        crisisYearsLeft: 0,
        crisisTotalYears: 0,
        crisisAge: 0,
        crisisSeverity: 0,
        crisisCooldownYears: 0,
        cycleMemory: { inventory: 0, investment: 0, infrastructure: 0, long_wave: 0 },
      };
      const rows = [];
      let previousRealIndex = simState.realIndex;

      for (let t = 0; t <= params.years; t += 1) {
        const feedback = feedbackByIndex[t] || {};
        const feedbackGrowth = clamp(Number(feedback.feedback_growth_impulse_pct || 0), -1.8, 1.05);
        const feedbackGap = clamp(Number(feedback.feedback_output_gap_impulse_pct || 0), -2.5, 1.8);
        const feedbackStress = clamp(Number(feedback.feedback_financial_stress_impulse || 0), -9, 18);
        const feedbackInflation = clamp(Number(feedback.feedback_inflation_impulse_pct || 0), -1.2, 1.6);
        const feedbackPolicy = clamp(Number(feedback.feedback_policy_impulse_pct || 0), -1.2, 1.4);
        const scenarioEventSeverity = clamp(Number(feedback.scenario_event_severity || 0), 0, 1.6);
        const scenarioPolicyImpulse = clamp(Number(feedback.scenario_policy_rate_impulse || 0), -1.5, 1.5);
        const scenarioLiquidityImpulse = clamp(Number(feedback.scenario_liquidity_impulse || 0), -1.8, 1.8);
        const scenarioCreditStress = clamp(Number(feedback.scenario_credit_stress_impulse || 0), -1.5, 1.8);
        const scenarioDollarPressure = clamp(Number(feedback.scenario_dollar_pressure_impulse || 0), -1.5, 1.8);
        const scenarioEnergyImpulse = clamp(Number(feedback.scenario_energy_price_impulse || 0), -1.8, 1.8);
        const scenarioLaggedSupport = clamp(Number(feedback.scenario_gdp_lagged_support || 0), -1.5, 1.5);
        const feedbackFields = {
          feedback_growth_impulse_pct: feedbackGrowth,
          feedback_output_gap_impulse_pct: feedbackGap,
          feedback_financial_stress_impulse: feedbackStress,
          feedback_inflation_impulse_pct: feedbackInflation,
          feedback_policy_impulse_pct: feedbackPolicy,
          feedback_source: feedback.feedback_source || "none",
        };
        const scenarioEventStub = scenarioEventSeverity > 0 ? {
          event_type: feedback.scenario_event_type || "branch_scenario",
          event_phase: feedback.scenario_event_phase || "branch_scenario",
          event_severity: scenarioEventSeverity,
          policy_rate_impulse: scenarioPolicyImpulse,
          liquidity_impulse: scenarioLiquidityImpulse,
          credit_stress_impulse: scenarioCreditStress,
          dollar_pressure_impulse: scenarioDollarPressure,
          energy_price_impulse: scenarioEnergyImpulse,
          gdp_lagged_support: scenarioLaggedSupport,
        } : {};
        if (t === 0) {
          rows.push(roundRow({
            year_index: t,
            year: params.startYear + t,
            seed,
            param_version: "global-gdp-cycle-v0.4-js",
            global_gdp_trillion_usd: params.initialGdp,
            real_gdp_index: simState.realIndex,
            potential_gdp_index: simState.potentialIndex,
            realized_growth_pct: params.baseTrendGrowth,
            potential_growth_pct: params.baseTrendGrowth,
            trend_growth_pct: params.baseTrendGrowth,
            cycle_growth_component_pct: 0,
            long_wave_component_pct: 0,
            infrastructure_component_pct: 0,
            investment_component_pct: 0,
            inventory_component_pct: 0,
            stochastic_component_pct: 0,
            shock_component_pct: 0,
            output_gap_pct: simState.outputGap,
            financial_stress_index: simState.financialStress,
            productivity_wave_index: 50 + 50 * sinWave(t, specs.longWave.period, specs.longWave.phase),
            crisis_intensity: 0,
            boom_intensity: 0,
            regime: "initial",
            ...emptyMacroEventStub(),
            ...scenarioEventStub,
            ...feedbackFields,
          }));
          continue;
        }

        const trendGrowth = longRunTrend(t, params, rng);
        const inventory = cycleComponent(t, specs.inventory, simState, rng);
        const investment = cycleComponent(t, specs.investment, simState, rng);
        const infrastructure = cycleComponent(t, specs.infrastructure, simState, rng);
        const longWave = cycleComponent(t, specs.longWave, simState, rng);
        const productivityWave = 50 + 50 * sinWave(t, specs.longWave.period, specs.longWave.phase);
        let potentialGrowth = trendGrowth + 0.35 * longWave + 0.15 * infrastructure;
        potentialGrowth = clamp(potentialGrowth, 0.15, 5.50);
        simState.potentialIndex *= 1 + potentialGrowth / 100;

        const cycleGrowth = inventory + investment + infrastructure + longWave;
        const stochastic = rng.gauss(0, 0.32 * params.volatilityScale);
        const event = drawEventShock(simState, params, rng, cycleGrowth);
        simState.shockStock = simState.shockStock * params.shockDecay + event.shock;
        const shock = simState.shockStock * params.shockReleaseSpeed;
        let stressTarget = 10 + Math.max(0, -shock) * 11 + Math.max(0, -cycleGrowth) * 5;
        stressTarget += rng.uniform(0, 9) * event.crisisIntensity;
        stressTarget += feedbackStress;
        simState.financialStress = clamp(
          smooth(simState.financialStress, stressTarget, 1 - params.financialStressDecay),
          0,
          100,
        );

        const stressDrag = -0.018 * Math.max(0, simState.financialStress - 45);
        const outputGapTarget = (
          simState.outputGap * params.outputGapPersistence
          + params.outputGapCycleLoading * cycleGrowth
          + params.outputGapShockLoading * shock
          + stochastic
          + stressDrag
          + feedbackGap
          + 0.45 * feedbackGrowth
        );
        simState.outputGap = clamp(
          smooth(simState.outputGap, outputGapTarget, params.outputGapAdjustmentSpeed),
          -params.outputGapCap,
          params.outputGapCap,
        );

        const desiredRealIndex = simState.potentialIndex * Math.exp(simState.outputGap / 100);
        let targetGrowth = pctChange(desiredRealIndex, previousRealIndex);
        targetGrowth += params.directCycleGrowthLoading * cycleGrowth;
        targetGrowth += params.directShockGrowthLoading * shock;
        targetGrowth += feedbackGrowth;
        targetGrowth = clamp(targetGrowth, simState.lastGrowth - params.maxGrowthStep, simState.lastGrowth + params.maxGrowthStep);
        let realizedGrowth = smooth(simState.lastGrowth, targetGrowth, params.growthAdjustmentSpeed);
        realizedGrowth = clamp(realizedGrowth, params.maxNegativeGrowth, params.maxPositiveGrowth);
        simState.realIndex = previousRealIndex * (1 + realizedGrowth / 100);
        previousRealIndex = simState.realIndex;
        simState.lastGrowth = realizedGrowth;
        const gdp = params.initialGdp * (simState.realIndex / params.initialIndex);
        const regime = classifyRegime(
          realizedGrowth,
          simState.outputGap,
          simState.financialStress,
          event.crisisIntensity,
          event.boomIntensity,
          event.phase,
        );
        const eventStub = buildMacroEventStub({
          regime,
          phase: event.phase,
          crisisIntensity: event.crisisIntensity,
          boomIntensity: event.boomIntensity,
          shock,
          outputGap: simState.outputGap,
          stress: simState.financialStress,
        });
        const eventStubWithScenario = scenarioEventSeverity > 0 ? {
          ...eventStub,
          event_type: feedback.scenario_event_type || eventStub.event_type,
          event_phase: feedback.scenario_event_phase || eventStub.event_phase,
          event_severity: Math.max(eventStub.event_severity || 0, scenarioEventSeverity),
          policy_rate_impulse: clamp((eventStub.policy_rate_impulse || 0) + scenarioPolicyImpulse, -2, 2),
          liquidity_impulse: clamp((eventStub.liquidity_impulse || 0) + scenarioLiquidityImpulse, -2.5, 2.5),
          credit_stress_impulse: clamp((eventStub.credit_stress_impulse || 0) + scenarioCreditStress, -2, 2.5),
          dollar_pressure_impulse: clamp((eventStub.dollar_pressure_impulse || 0) + scenarioDollarPressure, -2, 2.5),
          energy_price_impulse: clamp((eventStub.energy_price_impulse || 0) + scenarioEnergyImpulse, -2.5, 2.5),
          gdp_lagged_support: clamp((eventStub.gdp_lagged_support || 0) + scenarioLaggedSupport, -2, 2),
        } : eventStub;

        rows.push(roundRow({
          year_index: t,
          year: params.startYear + t,
          seed,
          param_version: "global-gdp-cycle-v0.4-js",
          global_gdp_trillion_usd: gdp,
          real_gdp_index: simState.realIndex,
          potential_gdp_index: simState.potentialIndex,
          realized_growth_pct: realizedGrowth,
          potential_growth_pct: potentialGrowth,
          trend_growth_pct: trendGrowth,
          cycle_growth_component_pct: cycleGrowth,
          long_wave_component_pct: longWave,
          infrastructure_component_pct: infrastructure,
          investment_component_pct: investment,
          inventory_component_pct: inventory,
          stochastic_component_pct: stochastic,
          shock_component_pct: shock,
          output_gap_pct: simState.outputGap,
          financial_stress_index: simState.financialStress,
          productivity_wave_index: productivityWave,
          crisis_intensity: event.crisisIntensity,
          boom_intensity: event.boomIntensity,
          regime,
          ...eventStubWithScenario,
          ...feedbackFields,
        }));
      }

      return rows;
    }

    function attachDynamicInflation(seed, rows) {
      const rng = makeRng((seed + 3100003) >>> 0);
      const stateInflation = {
        headline: 2.40 + rng.uniform(-0.25, 0.25),
        core: 2.25 + rng.uniform(-0.18, 0.18),
        expectation: 2.30 + rng.uniform(-0.12, 0.12),
        wage: 2.65 + rng.uniform(-0.20, 0.20),
        energyStock: 0,
        importStock: 0,
        supplyYearsLeft: 0,
        supplyTotalYears: 0,
        supplyAge: 0,
        supplySeverity: 0,
        supplyCooldown: 0,
      };

      function supplyShock(row) {
        if (stateInflation.supplyYearsLeft <= 0 && stateInflation.supplyCooldown > 0) {
          stateInflation.supplyCooldown -= 1;
        }
        if (stateInflation.supplyYearsLeft <= 0 && stateInflation.supplyCooldown <= 0) {
          const demandHeat = Math.max(0, row.realized_growth_pct - 2.8) + Math.max(0, row.output_gap_pct) * 0.35;
          if (rng.random() < 0.055 + demandHeat * 0.006) {
            stateInflation.supplyTotalYears = rng.randint(2, 5);
            stateInflation.supplyYearsLeft = stateInflation.supplyTotalYears;
            stateInflation.supplyAge = 0;
            stateInflation.supplySeverity = rng.uniform(0.65, 1.00);
          }
        }
        if (stateInflation.supplyYearsLeft <= 0) return 0;
        const progress = stateInflation.supplyAge / Math.max(1, stateInflation.supplyTotalYears - 1);
        let shape = Math.sin(Math.PI * clamp(progress, 0, 1));
        if (stateInflation.supplyTotalYears <= 2) shape = 1;
        const component = (1.10 + 2.40 * shape) * stateInflation.supplySeverity;
        stateInflation.supplyAge += 1;
        stateInflation.supplyYearsLeft -= 1;
        if (stateInflation.supplyYearsLeft <= 0) {
          stateInflation.supplyTotalYears = 0;
          stateInflation.supplyAge = 0;
          stateInflation.supplySeverity = 0;
          stateInflation.supplyCooldown = 5;
        }
        return component;
      }

      return rows.map((row) => {
        if (row.year_index === 0) {
          return roundRow({
            ...row,
            inflation_param_version: "global-inflation-layer-v0.1-js",
            inflation_interface_version: "inflation-feedback-interface-v0.1",
            headline_inflation_pct: stateInflation.headline,
            core_inflation_pct: stateInflation.core,
            energy_inflation_pct: 2.60,
            import_inflation_pct: 2.30,
            wage_pressure_pct: stateInflation.wage,
            inflation_expectation_pct: stateInflation.expectation,
            demand_pull_component_pct: 0,
            energy_component_pct: 0,
            external_supply_shock_component_pct: 0,
            import_component_pct: 0,
            liquidity_component_pct: 0,
            stress_disinflation_component_pct: 0,
            inflation_noise_component_pct: 0,
            monetary_tightening_pressure: 0,
            monetary_easing_pressure: 0,
            inflation_regime: "initial",
            inflation_to_policy_rate_impulse: 0,
            inflation_to_long_rate_impulse: 0,
            inflation_to_gdp_drag_placeholder: 0,
          });
        }

        const feedbackInflation = row.feedback_inflation_impulse_pct || 0;
        const growthSurprise = row.realized_growth_pct - row.potential_growth_pct;
        const demandPull = 0.18 * row.output_gap_pct + 0.20 * growthSurprise + 0.18 * row.boom_intensity + 0.08 * feedbackInflation;
        const externalSupply = supplyShock(row);
        stateInflation.energyStock = stateInflation.energyStock * 0.58 + (row.energy_price_impulse || 0) + 0.42 * feedbackInflation;
        stateInflation.importStock = stateInflation.importStock * 0.62 + (row.dollar_pressure_impulse || 0);
        const energyComponent = 0.92 * stateInflation.energyStock + externalSupply + rng.gauss(0, 0.55);
        const importComponent = 0.48 * stateInflation.importStock + 0.22 * externalSupply + rng.gauss(0, 0.25);
        const liquidityComponent = 0.36 * (row.liquidity_impulse || 0);
        const stressDisinflation = -0.24 * Math.max(0, row.financial_stress_index - 35) / 20 - 0.22 * Math.max(0, row.credit_stress_impulse || 0) - 0.34 * row.crisis_intensity;
        const noise = rng.gauss(0, 0.16);
        const wageTarget = 2.65 + 0.12 * row.output_gap_pct + 0.35 * Math.max(0, stateInflation.expectation - 2.25) - 0.18 * Math.max(0, row.financial_stress_index - 45) / 20;
        stateInflation.wage = clamp(smooth(stateInflation.wage, wageTarget, 0.30), -0.5, 7.0);
        const expectationTarget = 2.35 + 0.35 * (stateInflation.headline - 2.45) + 0.25 * (stateInflation.core - 2.30) + 0.08 * externalSupply + 0.12 * (row.liquidity_impulse || 0) + 0.08 * feedbackInflation - 0.10 * row.crisis_intensity;
        stateInflation.expectation = clamp(smooth(stateInflation.expectation, expectationTarget, 0.16), 0.4, 6.5);
        const coreTarget = 2.30 + demandPull + liquidityComponent + 0.26 * importComponent + 0.32 * (stateInflation.wage - 2.65) + 0.22 * (stateInflation.expectation - 2.35) + stressDisinflation + 0.16 * feedbackInflation + noise;
        stateInflation.core = clamp(smooth(stateInflation.core, coreTarget, 0.26), -0.5, 7.0);
        const energyInflation = clamp(2.45 + 3.0 * energyComponent + rng.gauss(0, 0.35), -8, 15);
        const importInflation = clamp(2.45 + 2.2 * importComponent + rng.gauss(0, 0.20), -4, 10);
        const headlineTarget = 0.62 * stateInflation.core + 0.28 * energyInflation + 0.10 * importInflation + 0.55 * feedbackInflation;
        stateInflation.headline = clamp(smooth(stateInflation.headline, headlineTarget, 0.44), -1.5, 9.5);
        const inflationGap = stateInflation.headline - 2.45;
        const tightening = clamp(18 * Math.max(0, inflationGap) + 5 * Math.max(0, row.output_gap_pct) - 3 * row.crisis_intensity, 0, 100);
        const easing = clamp(16 * Math.max(0, 2.45 - stateInflation.headline) + 5 * Math.max(0, -row.output_gap_pct) + 0.35 * row.financial_stress_index + 10 * row.crisis_intensity, 0, 100);
        let regime = "anchored_normal";
        if (stateInflation.headline < 0.5 && (row.financial_stress_index >= 45 || row.realized_growth_pct < 0.5)) regime = "deflationary_crisis";
        else if (stateInflation.headline >= 5.0 && row.realized_growth_pct < 1.4) regime = "stagflation_pressure";
        else if (stateInflation.headline >= 4.2 && row.output_gap_pct >= 1.5) regime = "overheating_inflation";
        else if (energyComponent >= 1.2 && stateInflation.headline >= 3.6) regime = "energy_cost_push";
        else if (row.event_type === "central_bank_easing_placeholder" && stateInflation.headline < 3.5) regime = "policy_reflation";
        else if (stateInflation.headline <= 1.4 && stateInflation.core <= 1.8) regime = "lowflation";
        else if (stateInflation.headline < stateInflation.core - 0.8) regime = "disinflation";

        return roundRow({
          ...row,
          inflation_param_version: "global-inflation-layer-v0.1-js",
          inflation_interface_version: "inflation-feedback-interface-v0.1",
          headline_inflation_pct: stateInflation.headline,
          core_inflation_pct: stateInflation.core,
          energy_inflation_pct: energyInflation,
          import_inflation_pct: importInflation,
          wage_pressure_pct: stateInflation.wage,
          inflation_expectation_pct: stateInflation.expectation,
          demand_pull_component_pct: demandPull,
          energy_component_pct: energyComponent,
          external_supply_shock_component_pct: externalSupply,
          import_component_pct: importComponent,
          liquidity_component_pct: liquidityComponent,
          stress_disinflation_component_pct: stressDisinflation,
          inflation_noise_component_pct: noise,
          monetary_tightening_pressure: tightening,
          monetary_easing_pressure: easing,
          inflation_regime: regime,
          inflation_to_policy_rate_impulse: clamp((tightening - easing) / 100, -1, 1),
          inflation_to_long_rate_impulse: clamp((0.60 * inflationGap + 0.20 * Math.max(0, stateInflation.expectation - 2.35)) / 4, -1, 1),
          inflation_to_gdp_drag_placeholder: clamp(-Math.max(0, inflationGap - 1.2) * 0.20, -1, 0),
        });
      });
    }

    function attachDynamicPolicy(rows) {
      const policyState = {
        policyRate: 3.25,
        previousPolicyRate: 3.25,
        qe: 8,
      };

      function classifyPolicy(row, policyChange, realPolicyRate, neutralPolicyRate, hikePressure, cutPressure) {
        if (row.crisis_intensity >= 0.65 || (row.financial_stress_index >= 55 && cutPressure >= 48)) return "emergency_easing";
        if (row.headline_inflation_pct >= 4.0 && row.realized_growth_pct < 1.5) return "stagflation_dilemma";
        if (policyChange >= 0.45 && hikePressure > cutPressure) return "hawkish_tightening";
        if (policyChange <= -0.45 && cutPressure >= hikePressure) return "rate_cut_cycle";
        if (policyState.qe >= 45 && realPolicyRate < neutralPolicyRate - 1.0) return "qe_repair";
        if (realPolicyRate > neutralPolicyRate + 1.0 && row.realized_growth_pct <= 2.0) return "restrictive_pause";
        if (row.headline_inflation_pct > 3.4 || row.core_inflation_pct > 3.0 || row.inflation_regime === "overheating_inflation") return "inflation_watch";
        if (row.output_gap_pct < -2.0 || cutPressure > hikePressure + 15) return "dovish_support";
        if (Math.abs(realPolicyRate - neutralPolicyRate) <= 0.55) return "neutral_hold";
        if (policyState.policyRate < neutralPolicyRate) return "accommodative_hold";
        return "mildly_restrictive";
      }

      return rows.map((row) => {
        const expectation = row.inflation_expectation_pct ?? 2.35;
        const realNeutral = clamp(0.75 + 0.18 * ((row.potential_growth_pct ?? 2) - 2) - 0.20 * Math.max(0, row.financial_stress_index - 35) / 40, -0.25, 2.25);
        const neutralPolicyRate = clamp(realNeutral + expectation, 0.35, 6.0);

        if (row.year_index === 0) {
          const realPolicyRate = policyState.policyRate - expectation;
          return roundRow({
            ...row,
            policy_param_version: "global-policy-rate-layer-v0.1-js",
            policy_interface_version: "policy-feedback-interface-v0.1",
            global_policy_rate_pct: policyState.policyRate,
            policy_reaction_target_rate_pct: neutralPolicyRate,
            neutral_policy_rate_pct: neutralPolicyRate,
            real_policy_rate_pct: realPolicyRate,
            shadow_policy_rate_pct: policyState.policyRate - 0.025 * policyState.qe,
            policy_rate_change_pct: 0,
            rate_hike_pressure: 0,
            rate_cut_pressure: 0,
            qe_liquidity_index: policyState.qe,
            balance_sheet_impulse: 0,
            policy_stance_index: realPolicyRate - realNeutral,
            central_bank_reaction_regime: "initial",
            policy_to_credit_tightening_impulse: 0,
            policy_to_dollar_pressure_impulse: 0,
            policy_to_equity_valuation_impulse: 0,
            policy_to_gdp_drag_placeholder: 0,
            policy_to_inflation_lagged_impulse: 0,
          });
        }

        const headlineGap = row.headline_inflation_pct - 2.35;
        const coreGap = row.core_inflation_pct - 2.20;
        const stressEasing = 0.035 * Math.max(0, row.financial_stress_index - 35);
        const crisisEasing = 1.10 * row.crisis_intensity;
        let targetRate = neutralPolicyRate + 0.42 * headlineGap + 0.78 * coreGap + 0.22 * row.output_gap_pct;
        targetRate += 1.35 * (row.inflation_to_policy_rate_impulse || 0) + 0.70 * (row.policy_rate_impulse || 0);
        targetRate += 0.60 * (row.feedback_policy_impulse_pct || 0);
        targetRate -= stressEasing + crisisEasing;
        targetRate = clamp(targetRate, 0.05, 8.50);
        const maxCut = row.crisis_intensity >= 0.65 ? 2.20 : 1.45;
        const desiredChange = clamp(targetRate - policyState.policyRate, -maxCut, 1.10);
        const newPolicyRate = clamp(smooth(policyState.policyRate, policyState.policyRate + desiredChange, 0.34), 0.05, 8.50);
        const policyChange = newPolicyRate - policyState.policyRate;
        policyState.previousPolicyRate = policyState.policyRate;
        policyState.policyRate = newPolicyRate;

        const hikePressure = clamp(0.55 * row.monetary_tightening_pressure + 12 * Math.max(0, headlineGap) + 16 * Math.max(0, coreGap) + 4 * Math.max(0, row.output_gap_pct), 0, 100);
        const cutPressure = clamp(0.60 * row.monetary_easing_pressure + 0.42 * row.financial_stress_index + 22 * row.crisis_intensity + 5 * Math.max(0, -row.output_gap_pct) + 8 * Math.max(0, 2.35 - row.headline_inflation_pct), 0, 100);

        let qeTarget = 0;
        if (policyState.policyRate <= 1.25 || cutPressure >= 42) {
          qeTarget = clamp(20 + 0.80 * Math.max(0, cutPressure - 42) + 35 * row.crisis_intensity - 0.40 * Math.max(0, hikePressure - cutPressure), 0, 100);
        }
        const oldQe = policyState.qe;
        if (qeTarget > policyState.qe) policyState.qe = smooth(policyState.qe, qeTarget, 0.34);
        else policyState.qe *= 0.78;
        policyState.qe = clamp(policyState.qe, 0, 100);
        const balanceSheetImpulse = policyState.qe - oldQe;
        const realPolicyRate = policyState.policyRate - expectation;
        const shadowPolicyRate = policyState.policyRate - 0.025 * policyState.qe;
        const stance = realPolicyRate - realNeutral - 0.018 * policyState.qe;
        const regime = classifyPolicy(row, policyChange, realPolicyRate, neutralPolicyRate, hikePressure, cutPressure);

        return roundRow({
          ...row,
          policy_param_version: "global-policy-rate-layer-v0.1-js",
          policy_interface_version: "policy-feedback-interface-v0.1",
          global_policy_rate_pct: policyState.policyRate,
          policy_reaction_target_rate_pct: targetRate,
          neutral_policy_rate_pct: neutralPolicyRate,
          real_policy_rate_pct: realPolicyRate,
          shadow_policy_rate_pct: shadowPolicyRate,
          policy_rate_change_pct: policyChange,
          rate_hike_pressure: hikePressure,
          rate_cut_pressure: cutPressure,
          qe_liquidity_index: policyState.qe,
          balance_sheet_impulse: balanceSheetImpulse,
          policy_stance_index: stance,
          central_bank_reaction_regime: regime,
          policy_to_credit_tightening_impulse: clamp(0.28 * stance + 0.55 * Math.max(0, policyChange) - 0.018 * policyState.qe, -2, 2),
          policy_to_dollar_pressure_impulse: clamp(0.22 * stance + 0.35 * policyChange - 0.010 * policyState.qe, -2, 2),
          policy_to_equity_valuation_impulse: clamp(-0.35 * stance - 0.45 * Math.max(0, policyChange) + 0.018 * policyState.qe, -2, 2),
          policy_to_gdp_drag_placeholder: clamp(-0.18 * Math.max(0, stance) - 0.15 * Math.max(0, policyChange), -1.5, 0.35),
          policy_to_inflation_lagged_impulse: clamp(-0.20 * Math.max(0, stance) - 0.12 * Math.max(0, policyChange) + 0.010 * policyState.qe, -1, 1),
        });
      });
    }

    function attachDynamicYieldCurve(rows) {
      const rng = makeRng(((rows[0]?.seed ?? 0) + 7200071) >>> 0);
      const curveState = {
        shortRate: 3.25,
        twoYear: 3.40,
        tenYear: 4.05,
        termPremium: 0.65,
        expectedShort10y: 3.35,
        bondIndex: 100,
        previousTenYear: 4.05,
        previousSpread: 0.65,
      };

      function classifyCurve(row, spread, tenYearChange, termPremiumChange, policyChange, stance, qe) {
        const spreadChange = spread - curveState.previousSpread;
        if (row.year_index === 0) return "initial";
        if (spread < -0.35 && stance > 0.25) return "inverted_tightening";
        if (row.crisis_intensity >= 0.60 && tenYearChange < -0.20) return "recession_bull_flattening";
        if (qe >= 45 && spread >= -0.20 && tenYearChange <= 0.15) return "qe_suppressed_curve";
        if (tenYearChange > 0.35 && termPremiumChange > 0.10 && row.headline_inflation_pct >= 3.2) return "bear_steepening";
        if (spreadChange > 0.35 && policyChange <= 0.05 && tenYearChange <= 0.20) return "bull_steepening";
        if (tenYearChange > 0.30 && spread < curveState.previousSpread - 0.15) return "bear_flattening";
        if (Math.abs(spread) <= 0.25) return "flat_curve";
        if (spread < 0) return "mild_inversion";
        if (row.financial_stress_index >= 55 && tenYearChange > 0.15) return "risk_premium_steepening";
        return "normal_upward_curve";
      }

      return rows.map((row) => {
        const policyRate = row.global_policy_rate_pct ?? 3.25;
        const policyChange = row.policy_rate_change_pct ?? 0;
        const neutralPolicy = row.neutral_policy_rate_pct ?? 3.25;
        const realPolicy = row.real_policy_rate_pct ?? 0;
        const stance = row.policy_stance_index ?? 0;
        const headline = row.headline_inflation_pct ?? 2.35;
        const expectation = row.inflation_expectation_pct ?? 2.25;
        const qe = row.qe_liquidity_index ?? 0;
        const balanceSheetImpulse = row.balance_sheet_impulse ?? 0;
        const hikePressure = row.rate_hike_pressure ?? 0;
        const cutPressure = row.rate_cut_pressure ?? 0;
        const inflationLongImpulse = row.inflation_to_long_rate_impulse ?? 0;

        const shortTarget = policyRate - 0.006 * qe + rng.gauss(0, 0.02);
        const shortRate = clamp(smooth(curveState.shortRate, shortTarget, 0.78), -0.35, 10.5);
        const expectedShortTarget = clamp(
          0.50 * neutralPolicy + 0.35 * policyRate + 0.15 * curveState.expectedShort10y + 0.012 * (hikePressure - cutPressure) + 0.15 * row.output_gap_pct - 0.40 * row.crisis_intensity - 0.010 * qe,
          -0.35,
          10.5,
        );
        const expectedShort10y = smooth(curveState.expectedShort10y, expectedShortTarget, 0.24);
        const termPremiumTarget = clamp(
          0.58 + 0.17 * Math.max(0, headline - 2.65) + 0.10 * Math.abs(inflationLongImpulse) + 0.018 * Math.max(0, row.financial_stress_index - 32) + 0.012 * Math.max(0, -balanceSheetImpulse) + 0.08 * Math.max(0, stance) - 0.020 * qe - 0.010 * Math.max(0, balanceSheetImpulse) + rng.gauss(0, 0.10),
          -0.45,
          2.80,
        );
        const termPremium = smooth(curveState.termPremium, termPremiumTarget, 0.30);
        const twoYearTarget = 0.62 * shortRate + 0.30 * policyRate + 0.08 * expectedShort10y + 0.20 * termPremium + 0.18 * policyChange + 0.006 * (hikePressure - cutPressure) - 0.28 * row.crisis_intensity - 0.006 * qe + rng.gauss(0, 0.07);
        const twoYear = clamp(smooth(curveState.twoYear, twoYearTarget, 0.56), -0.35, 10.5);
        const tenYearTarget = expectedShort10y + termPremium + 0.22 * (expectation - 2.25) + 0.35 * inflationLongImpulse + 0.08 * (row.potential_growth_pct - 2.0) - 0.42 * row.crisis_intensity - 0.006 * qe + rng.gauss(0, 0.09);
        const tenYear = clamp(smooth(curveState.tenYear, tenYearTarget, 0.34), -0.35, 10.5);
        const tenYearChange = tenYear - curveState.tenYear;
        const spread = tenYear - twoYear;
        const termPremiumChange = termPremium - curveState.termPremium;
        const real10y = tenYear - expectation;
        const durationPressure = clamp(7.4 * tenYearChange, -15, 15);
        const bondReturn = row.year_index === 0 ? 0 : clamp(curveState.previousTenYear - 7.4 * tenYearChange, -28, 24);
        const bondIndex = compoundIndexWithSoftDrag(curveState.bondIndex, bondReturn, 25, 240);
        const inversionPressure = clamp(32 * Math.max(0, -spread) + 9 * Math.max(0, stance) + 6 * Math.max(0, realPolicy - 1.0) + 9 * row.crisis_intensity, 0, 100);
        const regime = classifyCurve(row, spread, tenYearChange, termPremiumChange, policyChange, stance, qe);
        const dollarImpulse = clamp(0.22 * real10y + 0.18 * stance + 0.25 * Math.max(0, -spread) - 0.012 * qe, -2, 2);
        const equityImpulse = clamp(-0.30 * real10y - 0.70 * Math.max(0, tenYearChange) - 0.18 * Math.max(0, -spread) + 0.014 * qe, -2, 2);
        const creditImpulse = clamp(0.35 * Math.max(0, -spread) + 0.48 * Math.max(0, tenYearChange) + 0.20 * Math.max(0, termPremium - 0.75) + 0.12 * Math.max(0, stance) - 0.012 * qe, -2, 2);
        const gdpDrag = clamp(-0.16 * Math.max(0, real10y - 1.0) - 0.12 * Math.max(0, -spread) - 0.12 * Math.max(0, creditImpulse) + 0.006 * qe, -1.5, 0.45);

        const next = roundRow({
          ...row,
          yield_curve_param_version: "global-yield-curve-layer-v0.1-js",
          yield_curve_interface_version: "yield-curve-feedback-interface-v0.1",
          global_short_rate_pct: shortRate,
          global_2y_yield_pct: twoYear,
          global_10y_yield_pct: tenYear,
          global_real_10y_yield_pct: real10y,
          term_spread_10y_2y_pct: spread,
          term_premium_pct: termPremium,
          expected_short_rate_10y_pct: expectedShort10y,
          yield_curve_reference_10y_bond_total_return_index: bondIndex,
          yield_curve_reference_10y_bond_total_return_pct: bondReturn,
          duration_pressure_index: durationPressure,
          curve_inversion_pressure: inversionPressure,
          yield_curve_regime: regime,
          yield_curve_to_dollar_impulse: dollarImpulse,
          yield_curve_to_equity_valuation_impulse: equityImpulse,
          yield_curve_to_credit_impulse: creditImpulse,
          yield_curve_to_gdp_drag_placeholder: gdpDrag,
        });

        curveState.shortRate = shortRate;
        curveState.twoYear = twoYear;
        curveState.previousTenYear = curveState.tenYear;
        curveState.tenYear = tenYear;
        curveState.termPremium = termPremium;
        curveState.expectedShort10y = expectedShort10y;
        curveState.bondIndex = bondIndex;
        curveState.previousSpread = spread;
        return next;
      });
    }

    function attachDynamicDollarLiquidity(rows) {
      const rng = makeRng(((rows[0]?.seed ?? 0) + 9500117) >>> 0);
      const dollarState = {
        dollar: 100,
        liquidity: 55,
        fci: 0,
        risk: 50,
        emStress: 35,
        fundingStress: 35,
      };

      function classifyDollar(row, dollar, momentum, liquidity, impulse, fci, risk, emStress, fundingStress) {
        if (row.year_index === 0) return "initial";
        if (row.crisis_intensity >= 0.55 && momentum > 0.5 && fundingStress >= 50) return "crisis_dollar_squeeze";
        if (dollar >= 106 && risk < 42) return "safe_haven_dollar_bid";
        if (impulse >= 7 && row.qe_liquidity_index >= 35 && momentum <= 1.5) return "liquidity_easing_reflation";
        if (fci >= 1.75) return "tight_financial_conditions";
        if (dollar <= 96 && liquidity >= 62 && risk >= 55) return "dollar_bear_liquidity_wave";
        if (liquidity >= 64 && risk >= 58) return "risk_on_liquidity_expansion";
        if (emStress >= 62 && dollar >= 103) return "em_dollar_pressure";
        if (dollar >= 104 && fci >= 0.75) return "disinflationary_dollar_strength";
        if (dollar <= 97 && fci <= -0.35) return "easy_dollar_liquidity";
        return "neutral_dollar_liquidity";
      }

      return rows.map((row) => {
        const real10y = row.global_real_10y_yield_pct ?? 0;
        const policyStance = row.policy_stance_index ?? 0;
        const stress = row.financial_stress_index ?? 35;
        const qe = row.qe_liquidity_index ?? 0;
        const balanceSheetImpulse = row.balance_sheet_impulse ?? 0;
        const realPolicy = row.real_policy_rate_pct ?? 0;
        const inversionPressure = row.curve_inversion_pressure ?? 0;
        const termPremium = row.term_premium_pct ?? 0.6;
        const termSpread = row.term_spread_10y_2y_pct ?? 0;
        const tenYearChange = (row.duration_pressure_index ?? 0) / 7.4;
        const safeHaven = clamp(row.crisis_intensity + Math.max(0, stress - 48) / 52, 0, 1.6);

        const dollarTarget = 100 + 3.20 * real10y + 2.15 * policyStance + 7.80 * safeHaven + 0.10 * Math.max(0, stress - 35) + 0.060 * inversionPressure + 4.25 * (row.yield_curve_to_dollar_impulse || 0) - 0.045 * qe - 0.60 * Math.max(0, row.realized_growth_pct - row.potential_growth_pct) + rng.gauss(0, 0.85);
        const dollar = clamp(smooth(dollarState.dollar, dollarTarget, 0.30), 82, 124);
        const dollarYoy = pctChange(dollar, dollarState.dollar);
        const momentum = clamp(dollarYoy * 2.2 + (dollar - 100) * 0.22, -20, 20);
        const liquidityTarget = 55 + 0.58 * qe + 0.36 * balanceSheetImpulse - 4.15 * Math.max(0, real10y) - 1.35 * Math.max(0, realPolicy) - 0.30 * Math.max(0, dollar - 100) - 0.20 * Math.max(0, stress - 35) - 3.0 * Math.max(0, termPremium - 0.75) + 1.5 * Math.max(0, -termSpread) + rng.gauss(0, 0.55);
        const liquidity = clamp(smooth(dollarState.liquidity, liquidityTarget, 0.34), 0, 100);
        const liquidityImpulse = liquidity - dollarState.liquidity;
        const fciTarget = 0.040 * (dollar - 100) + 0.38 * real10y + 0.26 * policyStance + 0.024 * Math.max(0, stress - 35) + 0.014 * inversionPressure + 0.36 * (row.yield_curve_to_credit_impulse || 0) + 0.24 * Math.max(0, tenYearChange) - 0.030 * (liquidity - 50) - 0.018 * qe;
        const fci = clamp(smooth(dollarState.fci, fciTarget, 0.42), -4, 4);
        const riskTarget = 50 - 7.80 * fci - 0.30 * Math.max(0, stress - 35) - 16.0 * row.crisis_intensity + 2.60 * (row.realized_growth_pct - row.potential_growth_pct) + 0.28 * (liquidity - 50) - 0.16 * Math.max(0, dollar - 100) + 5.0 * Math.max(0, row.yield_curve_to_equity_valuation_impulse || 0) + rng.gauss(0, 0.85);
        const risk = clamp(smooth(dollarState.risk, riskTarget, 0.36), 0, 100);
        const emStressTarget = 34 + 0.86 * Math.max(0, dollar - 100) + 1.35 * Math.max(0, momentum) + 8.5 * Math.max(0, fci) + 0.28 * Math.max(0, stress - 35) + 16.0 * row.crisis_intensity - 0.20 * (liquidity - 50) - 0.16 * Math.max(0, row.output_gap_pct);
        const emStress = clamp(smooth(dollarState.emStress, emStressTarget, 0.36), 0, 100);
        const fundingTarget = 32 + 0.42 * stress + 1.15 * Math.max(0, momentum) + 0.55 * inversionPressure + 9.0 * Math.max(0, fci) + 15.0 * row.crisis_intensity - 0.24 * liquidity;
        const fundingStress = clamp(smooth(dollarState.fundingStress, fundingTarget, 0.40), 0, 100);
        const regime = classifyDollar(row, dollar, momentum, liquidity, liquidityImpulse, fci, risk, emStress, fundingStress);
        const importInflationImpulse = clamp(-0.018 * (dollar - 100) - 0.030 * momentum, -1, 1);
        const oilPressure = clamp(-0.015 * (dollar - 100) - 0.032 * momentum + 0.018 * (risk - 50) + 0.008 * liquidityImpulse, -1.5, 1.5);
        const gdpDrag = clamp(-0.045 * Math.max(0, dollar - 102) - 0.060 * Math.max(0, fci) - 0.010 * Math.max(0, emStress - 50), -1.5, 0.35);
        const creditTightening = clamp(0.030 * Math.max(0, dollar - 100) + 0.045 * Math.max(0, momentum) + 0.25 * Math.max(0, fci) + 0.012 * Math.max(0, fundingStress - 45), -1, 2);
        const equityImpulse = clamp(0.030 * (liquidity - 50) + 0.028 * (risk - 50) - 0.40 * Math.max(0, fci) - 0.025 * Math.max(0, dollar - 103), -2, 2);
        const creditEasing = clamp(0.026 * (liquidity - 50) - 0.30 * Math.max(0, fci) - 0.018 * Math.max(0, fundingStress - 45), -2, 2);

        const next = roundRow({
          ...row,
          dollar_liquidity_param_version: "global-dollar-liquidity-layer-v0.1-js",
          dollar_liquidity_interface_version: "dollar-liquidity-feedback-interface-v0.1",
          global_dollar_index: dollar,
          dollar_yoy_change_pct: dollarYoy,
          dollar_momentum_index: momentum,
          global_liquidity_index: liquidity,
          liquidity_impulse_index: liquidityImpulse,
          global_financial_conditions_index: fci,
          risk_appetite_index: risk,
          em_stress_index: emStress,
          dollar_funding_stress_index: fundingStress,
          dollar_liquidity_regime: regime,
          dollar_to_import_inflation_impulse: importInflationImpulse,
          dollar_to_oil_pressure_impulse: oilPressure,
          dollar_to_gdp_drag_placeholder: gdpDrag,
          dollar_to_credit_tightening_impulse: creditTightening,
          liquidity_to_equity_impulse: equityImpulse,
          liquidity_to_credit_easing_impulse: creditEasing,
        });

        dollarState.dollar = dollar;
        dollarState.liquidity = liquidity;
        dollarState.fci = fci;
        dollarState.risk = risk;
        dollarState.emStress = emStress;
        dollarState.fundingStress = fundingStress;
        return next;
      });
    }

    function attachDynamicCreditSpreads(rows) {
      const rng = makeRng(((rows[0]?.seed ?? 0) + 12700091) >>> 0);
      const creditState = {
        ig: 115,
        hy: 420,
        weighted: 0.35 * 115 + 0.65 * 420,
        defaultRisk: 30,
        lending: 42,
        bankStress: 35,
        bankSentiment: 54,
        bankBalanceStress: 34,
        impairment: 0,
      };

      function classifyCredit(row, hy, ig, spreadChange, defaultRisk, lending, availability, refinancing, bankStress, bankSentiment, bankBalanceStress, convexityPressure, impairment) {
        if (row.year_index === 0) return "initial";
        if (row.crisis_intensity >= 0.65 && (hy >= 850 || defaultRisk >= 72 || convexityPressure >= 35)) return "recession_default_wave";
        if (bankBalanceStress >= 78 && bankSentiment <= 24) return "bank_lending_freeze";
        if (impairment >= 32 && bankSentiment <= 52) return "balance_sheet_repair";
        if (bankStress >= 68 && spreadChange >= 55) return "funding_stress_credit_shock";
        if (convexityPressure >= 45 && spreadChange >= 35) return "convex_credit_selloff";
        if (hy >= 720 && row.global_financial_conditions_index >= 1.0) return "credit_squeeze";
        if (spreadChange >= 65 && row.global_financial_conditions_index >= 0.50) return "rapid_spread_widening";
        if (row.liquidity_impulse_index >= 5 && spreadChange <= -35 && impairment <= 24) return "credit_easing_repair";
        if (hy <= 340 && ig <= 95 && row.risk_appetite_index >= 64 && row.global_liquidity_index >= 62 && impairment <= 14) return "credit_goldilocks";
        if (refinancing >= 65 && availability <= 42) return "refinancing_wall";
        if (hy <= 420 && lending >= 55 && row.global_financial_conditions_index > 0) return "late_cycle_tightening";
        if (availability >= 66 && row.risk_appetite_index >= 58 && hy <= 520 && bankSentiment >= 55 && impairment <= 18) return "easy_credit_expansion";
        return "normal_credit_cycle";
      }

      return rows.map((row) => {
        const growthShortfall = Math.max(0, row.potential_growth_pct - row.realized_growth_pct);
        const recessionSignal = Math.max(0, -row.realized_growth_pct);
        const negativeGap = Math.max(0, -row.output_gap_pct);
        const impairmentMemory = creditState.impairment;
        const creditTighteningStack = 0.70 * (row.policy_to_credit_tightening_impulse || 0) + 0.85 * (row.yield_curve_to_credit_impulse || 0) + 1.10 * (row.dollar_to_credit_tightening_impulse || 0) - 0.85 * (row.liquidity_to_credit_easing_impulse || 0);

        const defaultTarget = 24 + 5.2 * growthShortfall + 8.5 * recessionSignal + 2.2 * negativeGap + 0.36 * Math.max(0, row.financial_stress_index - 32) + 14 * row.crisis_intensity + 6 * Math.max(0, row.global_financial_conditions_index) + 7 * Math.max(0, creditTighteningStack) + 2.2 * Math.max(0, row.global_real_10y_yield_pct || 0) + 0.06 * impairmentMemory - 0.16 * Math.max(0, row.global_liquidity_index - 50) - 0.12 * Math.max(0, row.risk_appetite_index - 50);
        const defaultRisk = clamp(smooth(creditState.defaultRisk, defaultTarget, 0.34), 0, 100);
        const lendingTarget = 38 + 0.34 * row.dollar_funding_stress_index + 0.18 * row.em_stress_index + 4.8 * Math.max(0, row.global_financial_conditions_index) + 0.28 * row.curve_inversion_pressure + 6.5 * Math.max(0, creditTighteningStack) + 0.24 * Math.max(0, row.global_dollar_index - 100) + 0.20 * Math.max(0, row.dollar_momentum_index) + 0.22 * Math.max(0, row.financial_stress_index - 35) + 0.06 * impairmentMemory - 0.26 * Math.max(0, row.global_liquidity_index - 50) - 0.18 * Math.max(0, row.liquidity_impulse_index);
        const lending = clamp(smooth(creditState.lending, lendingTarget, 0.36), 0, 100);
        const bankTarget = 26 + 0.46 * row.dollar_funding_stress_index + 0.28 * row.financial_stress_index + 0.22 * row.em_stress_index + 5.5 * Math.max(0, row.global_financial_conditions_index) + 0.16 * row.curve_inversion_pressure + 4.0 * Math.max(0, row.term_premium_pct - 0.75) + 0.08 * impairmentMemory - 0.22 * Math.max(0, row.global_liquidity_index - 50);
        const bankStress = clamp(smooth(creditState.bankStress, bankTarget, 0.36), 0, 100);
        const real10y = row.global_real_10y_yield_pct || 0;
        const igTarget = 60 + 1.25 * defaultRisk + 0.90 * lending + 0.85 * row.dollar_funding_stress_index + 12 * Math.max(0, row.global_financial_conditions_index) + 18 * Math.max(0, creditTighteningStack) + 0.20 * impairmentMemory + 5 * Math.max(0, real10y) - 0.65 * row.global_liquidity_index - 0.28 * row.risk_appetite_index + rng.gauss(0, 5.4);
        const ig = clamp(smooth(creditState.ig, igTarget, 0.30), 35, 650);
        const hyTarget = 245 + 4.45 * defaultRisk + 3.65 * lending + 2.55 * row.dollar_funding_stress_index + 36 * Math.max(0, row.global_financial_conditions_index) + 72 * Math.max(0, creditTighteningStack) + 145 * row.crisis_intensity + 0.95 * impairmentMemory + 22 * Math.max(0, real10y) + 18 * growthShortfall - 2.40 * row.global_liquidity_index - 1.20 * row.risk_appetite_index + rng.gauss(0, 12);
        const hy = clamp(smooth(creditState.hy, hyTarget, 0.32), 150, 2200);
        const hyIgGap = Math.max(0, hy - ig);
        const convexityPressure = piecewiseCreditConvexityPressure(hy);
        const bankBalanceTarget = 20 + 0.32 * bankStress + 0.26 * defaultRisk + 0.022 * Math.max(0, hy - 500) + 0.012 * Math.max(0, hyIgGap - 300) + 0.22 * Math.max(0, row.dollar_funding_stress_index - 35) + 0.25 * convexityPressure + 0.12 * impairmentMemory - 0.16 * Math.max(0, row.qe_liquidity_index - 25) - 0.16 * Math.max(0, row.global_liquidity_index - 55);
        const bankBalanceStress = clamp(smooth(creditState.bankBalanceStress, bankBalanceTarget, 0.34), 0, 100);
        const bankSentimentTarget = 78 - 0.24 * lending - 0.22 * defaultRisk - 0.18 * bankBalanceStress - 0.012 * Math.max(0, hy - 500) - 0.010 * Math.max(0, hyIgGap - 300) - 0.14 * convexityPressure - 0.12 * impairmentMemory + 0.18 * Math.max(0, row.global_liquidity_index - 50) + 0.14 * Math.max(0, row.qe_liquidity_index - 20) + 0.09 * Math.max(0, row.risk_appetite_index - 50);
        const bankSentiment = clamp(smooth(creditState.bankSentiment, bankSentimentTarget, 0.34), 0, 100);
        const weighted = 0.35 * ig + 0.65 * hy;
        const spreadChange = weighted - creditState.weighted;
        const spreadIndex = clamp((ig - 70) / 4.2 + (hy - 280) / 13 + 0.22 * defaultRisk + 0.16 * lending, 0, 100);
        const availability = clamp(100 - 0.56 * lending - 0.35 * defaultRisk - 0.16 * Math.max(0, hy - 420) / 10 - 0.22 * Math.max(0, bankBalanceStress - 45) - 0.12 * impairmentMemory + 0.30 * Math.max(0, bankSentiment - 50) + 0.28 * (row.global_liquidity_index - 50) + 0.12 * Math.max(0, row.risk_appetite_index - 50), 0, 100);
        const impairmentInflow = clamp(0.025 * Math.max(0, hy - 560) + 0.12 * Math.max(0, defaultRisk - 58) + 0.10 * Math.max(0, lending - 58) + 0.10 * Math.max(0, bankBalanceStress - 55) + 0.08 * Math.max(0, spreadChange) + 1.80 * recessionSignal + 0.35 * Math.max(0, negativeGap - 2) + 8.0 * Math.max(0, row.crisis_intensity - 0.45), 0, 28);
        const repairRelief = 0.12 * Math.max(0, availability - 55) + 0.10 * Math.max(0, bankSentiment - 52) + 0.08 * Math.max(0, row.liquidity_impulse_index) + 0.03 * Math.max(0, row.global_liquidity_index - 60);
        const impairment = clamp(impairmentMemory * 0.84 + impairmentInflow - repairRelief, 0, 100);
        const refinancing = clamp(0.035 * Math.max(0, hy - 350) + 0.026 * Math.max(0, ig - 110) + 7 * Math.max(0, real10y) + 0.24 * row.dollar_funding_stress_index + 0.22 * Math.max(0, row.global_dollar_index - 100) + 8 * Math.max(0, row.global_financial_conditions_index) + 0.08 * impairment - 0.18 * Math.max(0, row.global_liquidity_index - 50), 0, 100);
        const regime = classifyCredit(row, hy, ig, spreadChange, defaultRisk, lending, availability, refinancing, bankStress, bankSentiment, bankBalanceStress, convexityPressure, impairment);
        const gdpDrag = clamp(piecewiseCreditGdpDrag(hy) - 0.0040 * Math.max(0, ig - 120) - 0.012 * Math.max(0, lending - 55) - 0.012 * Math.max(0, 50 - bankSentiment) - 0.007 * Math.max(0, bankBalanceStress - 55) - 0.005 * impairment + 0.004 * Math.max(0, availability - 65), -3.5, 0.35);
        const equityRiskPremium = clamp(0.0060 * Math.max(0, hy - 350) + 0.010 * Math.max(0, defaultRisk - 45) + 0.008 * Math.max(0, bankStress - 50) + 0.006 * Math.max(0, bankBalanceStress - 55) + 0.004 * convexityPressure + 0.003 * impairment - 0.006 * Math.max(0, row.global_liquidity_index - 60), -1, 2.5);
        const policyEasing = clamp(0.010 * Math.max(0, hy - 520) + 0.012 * Math.max(0, defaultRisk - 55) + 0.010 * Math.max(0, lending - 60) + 0.006 * Math.max(0, bankBalanceStress - 60) + 0.004 * Math.max(0, impairment - 25) + 0.50 * row.crisis_intensity, 0, 2);
        const inflationDrag = clamp(-0.006 * Math.max(0, hy - 500) - 0.012 * Math.max(0, defaultRisk - 55) - 0.006 * Math.max(0, 50 - bankSentiment) - 0.002 * impairment + 0.004 * Math.max(0, availability - 65), -1.5, 0.25);
        const oilDemand = clamp(-0.0045 * Math.max(0, hy - 450) - 0.012 * Math.max(0, defaultRisk - 50) - 0.006 * Math.max(0, 50 - bankSentiment) - 0.002 * impairment + 0.005 * Math.max(0, availability - 65), -1.5, 0.35);

        const next = roundRow({
          ...row,
          credit_spread_param_version: "global-credit-spread-layer-v0.2-js",
          credit_spread_interface_version: "credit-spread-feedback-interface-v0.2",
          global_investment_grade_spread_bps: ig,
          global_high_yield_spread_bps: hy,
          global_credit_spread_index: spreadIndex,
          credit_spread_change_bps: spreadChange,
          default_risk_index: defaultRisk,
          lending_standards_index: lending,
          credit_availability_index: availability,
          corporate_refinancing_pressure_index: refinancing,
          bank_credit_stress_index: bankStress,
          bank_lending_sentiment_index: bankSentiment,
          bank_balance_sheet_stress_index: bankBalanceStress,
          credit_convexity_pressure_index: convexityPressure,
          credit_impairment_stock_index: impairment,
          credit_regime: regime,
          credit_to_gdp_drag_placeholder: gdpDrag,
          credit_to_equity_risk_premium_impulse: equityRiskPremium,
          credit_to_policy_easing_pressure: policyEasing,
          credit_to_inflation_demand_drag_placeholder: inflationDrag,
          credit_to_oil_demand_impulse: oilDemand,
        });

        creditState.ig = ig;
        creditState.hy = hy;
        creditState.weighted = weighted;
        creditState.defaultRisk = defaultRisk;
        creditState.lending = lending;
        creditState.bankStress = bankStress;
        creditState.bankSentiment = bankSentiment;
        creditState.bankBalanceStress = bankBalanceStress;
        creditState.impairment = impairment;
        return next;
      });
    }

    function attachDynamicAssetPrices(rows) {
      const rng = makeRng(((rows[0]?.seed ?? 0) + 15300181) >>> 0);
      const assetState = {
        equity: 100,
        earnings: 100,
        pe: 18,
        peak: 100,
        sovereignBond: 100,
        corporateBond: 100,
        portfolio: 100,
        previousIg: 115,
      };

      function classifyAsset(row, equityReturn, sovereignReturn, corporateReturn, peChange, drawdown) {
        if (row.year_index === 0) return "initial";
        if (equityReturn <= -18 && (row.global_high_yield_spread_bps >= 850 || row.crisis_intensity >= 0.65)) return "equity_credit_crash";
        if (equityReturn <= -5 && sovereignReturn <= -3 && row.headline_inflation_pct >= 3.5) return "stock_bond_inflation_shock";
        if (sovereignReturn >= 8 && equityReturn <= 0) return "bond_rally_recession_hedge";
        if (equityReturn >= 9 && row.global_liquidity_index >= 64 && row.risk_appetite_index >= 56) return "liquidity_equity_bull";
        if (equityReturn >= 6 && sovereignReturn >= 0 && row.headline_inflation_pct <= 3.4) return "goldilocks_asset_rally";
        if (drawdown <= -25 && equityReturn > 6) return "bear_market_rebound";
        if (peChange <= -0.8 && row.global_real_10y_yield_pct >= 0.8) return "valuation_compression";
        if (["credit_squeeze", "funding_stress_credit_shock", "recession_default_wave"].includes(row.credit_regime) && corporateReturn < sovereignReturn) return "credit_drag_risk_off";
        if (equityReturn <= -6) return "equity_risk_off";
        if (corporateReturn >= 5 && equityReturn >= 3) return "credit_beta_rally";
        return "normal_asset_cycle";
      }

      return rows.map((row) => {
        const creditImpairment = row.credit_impairment_stock_index || 0;
        const marginPressure = Math.max(0, row.headline_inflation_pct - 4) * 0.65 + Math.max(0, row.core_inflation_pct - 3.5) * 0.35;
        const earningsTarget = 2.65 + 1.15 * row.realized_growth_pct + 0.28 * row.headline_inflation_pct + 0.42 * row.output_gap_pct - 1.20 * Math.max(0, row.potential_growth_pct - row.realized_growth_pct) - 2.20 * Math.max(0, -row.realized_growth_pct) - marginPressure - 0.009 * Math.max(0, row.global_high_yield_spread_bps - 450) - 0.025 * creditImpairment - 0.40 * Math.max(0, row.global_dollar_index - 103) + rng.gauss(0, 0.80);
        const epsGrowth = clamp(smooth(0, earningsTarget, 0.62), -24, 28);
        const earnings = clamp(assetState.earnings * (1 + epsGrowth / 100), 45, 460);
        const equityRiskPremium = clamp(4.8 + 0.018 * Math.max(0, row.global_high_yield_spread_bps - 420) + 0.035 * Math.max(0, row.default_risk_index - 35) + 0.42 * Math.max(0, row.global_financial_conditions_index) + 0.65 * Math.max(0, row.credit_to_equity_risk_premium_impulse) + 0.007 * creditImpairment - 0.012 * Math.max(0, row.global_liquidity_index - 55) - 0.018 * Math.max(0, row.risk_appetite_index - 50), 2.5, 12);
        const peTarget = clamp(21.5 - 1.25 * Math.max(0, row.global_real_10y_yield_pct) - 0.0012 * Math.max(0, row.global_high_yield_spread_bps - 420) - 0.55 * Math.max(0, row.global_financial_conditions_index) - 0.65 * Math.max(0, row.policy_stance_index) - 0.030 * Math.max(0, row.global_dollar_index - 100) - 0.85 * Math.max(0, row.credit_to_equity_risk_premium_impulse) - 0.018 * creditImpairment + 0.075 * (row.global_liquidity_index - 55) + 0.065 * (row.risk_appetite_index - 50) + 0.70 * Math.max(0, row.yield_curve_to_equity_valuation_impulse) + 0.55 * Math.max(0, row.liquidity_to_equity_impulse) + rng.gauss(0, 0.32), 8.5, 32);
        const pe = smooth(assetState.pe, peTarget, 0.32);
        const peChange = pe - assetState.pe;
        const fairEquity = earnings * pe / 18;
        const equityPrice = clamp(smooth(assetState.equity, fairEquity, 0.42), 20, 520);
        const equityReturn = row.year_index === 0 ? 0 : clamp(pctChange(equityPrice, assetState.equity) + 3.00, -45, 55);
        const equity = clamp(assetState.equity * (1 + equityReturn / 100), 20, 620);
        const peak = Math.max(assetState.peak, equity);
        const drawdown = clamp((equity / Math.max(1e-9, peak) - 1) * 100, -90, 0);
        const sovereignReturn = row.year_index === 0 ? 0 : clamp(0.68 * row.yield_curve_reference_10y_bond_total_return_pct - 0.35 * Math.max(0, row.headline_inflation_pct - 4) + 0.20 * Math.max(0, row.crisis_intensity - 0.35) * 10, -26, 24);
        const sovereignBond = compoundIndexWithSoftDrag(assetState.sovereignBond, sovereignReturn, 30, 240);
        const igChange = row.global_investment_grade_spread_bps - assetState.previousIg;
        const corporateReturn = row.year_index === 0 ? 0 : clamp(0.55 * sovereignReturn + 0.48 * row.global_10y_yield_pct + 0.60 * (row.global_investment_grade_spread_bps / 100) - 4.2 * (igChange / 100) - 0.55 * Math.max(0, row.credit_spread_change_bps / 100), -30, 24);
        const corporateBond = compoundIndexWithSoftDrag(assetState.corporateBond, corporateReturn, 25, 240);
        const portfolioReturn = 0.60 * equityReturn + 0.40 * sovereignReturn;
        const portfolio = compoundIndexWithSoftDrag(assetState.portfolio, portfolioReturn, 25, 360);
        const assetVolatility = clamp(12 + 0.55 * Math.abs(equityReturn) + 0.30 * Math.abs(sovereignReturn) + 0.16 * Math.max(0, row.global_high_yield_spread_bps - 420) / 10 + 0.20 * Math.max(0, 50 - row.risk_appetite_index) + 0.12 * creditImpairment + 15 * row.crisis_intensity, 5, 100);
        const regime = classifyAsset(row, equityReturn, sovereignReturn, corporateReturn, peChange, drawdown);
        const wealthImpulse = clamp(0.018 * Math.max(-25, Math.min(25, equityReturn)) + 0.006 * Math.max(-18, Math.min(18, sovereignReturn)) - 0.012 * Math.max(0, -drawdown - 15), -1.5, 1.2);
        const policyFciImpulse = clamp(-0.012 * Math.max(0, equityReturn) + 0.020 * Math.max(0, -equityReturn) + 0.018 * Math.max(0, -sovereignReturn) + 0.012 * Math.max(0, assetVolatility - 35), -1, 1.5);
        const creditRiskAppetite = clamp(0.018 * equityReturn + 0.006 * corporateReturn - 0.010 * Math.max(0, assetVolatility - 30), -1.5, 1.5);
        const inflationWealth = clamp(0.010 * Math.max(0, equityReturn) + 0.004 * Math.max(0, portfolioReturn) - 0.012 * Math.max(0, -equityReturn), -0.8, 0.8);

        const next = roundRow({
          ...row,
          asset_price_param_version: "global-asset-price-layer-v0.1-js",
          asset_price_interface_version: "asset-price-feedback-interface-v0.1",
          asset_accounting_authority: "non_authoritative_scenario_sketch",
          global_equity_price_index: equity,
          global_equity_price_return_pct: equityReturn,
          global_equity_total_return_pct: equityReturn,
          global_equity_eps_index: earnings,
          global_equity_eps_growth_pct: epsGrowth,
          global_equity_valuation_pe: pe,
          equity_risk_premium_pct: equityRiskPremium,
          global_equity_drawdown_pct: drawdown,
          global_sovereign_bond_total_return_index: sovereignBond,
          global_sovereign_bond_total_return_pct: sovereignReturn,
          global_corporate_bond_total_return_index: corporateBond,
          global_corporate_bond_total_return_pct: corporateReturn,
          global_60_40_total_return_index: portfolio,
          global_60_40_total_return_pct: portfolioReturn,
          asset_volatility_index: assetVolatility,
          asset_risk_regime: regime,
          asset_to_gdp_wealth_impulse: wealthImpulse,
          asset_to_policy_financial_conditions_impulse: policyFciImpulse,
          asset_to_credit_risk_appetite_impulse: creditRiskAppetite,
          asset_to_inflation_wealth_demand_impulse: inflationWealth,
        });

        assetState.equity = equity;
        assetState.earnings = earnings;
        assetState.pe = pe;
        assetState.peak = peak;
        assetState.sovereignBond = sovereignBond;
        assetState.corporateBond = corporateBond;
        assetState.portfolio = portfolio;
        assetState.previousIg = row.global_investment_grade_spread_bps;
        return next;
      });
    }

    function attachDynamicOilCommodities(rows) {
      const rng = makeRng(((rows[0]?.seed ?? 0) + 18400111) >>> 0);
      const oilState = {
        brent: 82,
        oilIndex: 100,
        commodityIndex: 100,
        oilReturn: 0,
        commodityReturn: 0,
        demand: 50,
        supplyShock: 0,
        inventoryPressure: 0,
        energyPressure: 50,
        supplyEventYearsLeft: 0,
        supplyEventTarget: 0,
      };

      function maybeUpdateSupplyEvent(row) {
        if (row.year_index === 0) {
          oilState.supplyEventTarget = 0;
          oilState.supplyEventYearsLeft = 0;
          return;
        }
        if (oilState.supplyEventYearsLeft > 0) {
          oilState.supplyEventYearsLeft -= 1;
          return;
        }
        oilState.supplyEventTarget *= 0.45;
        const shortageChance = 0.055 + 0.025 * row.crisis_intensity + 0.008 * Math.max(0, row.headline_inflation_pct - 4) + 0.012 * Math.max(0, row.energy_price_impulse);
        const glutChance = 0.025 + 0.010 * Math.max(0, 1 - row.realized_growth_pct) + 0.002 * Math.max(0, 100 - row.global_dollar_index) + 0.008 * Math.max(0, -row.energy_price_impulse);
        const roll = rng.random();
        if (roll < shortageChance) {
          oilState.supplyEventYearsLeft = rng.randint(1, 4);
          oilState.supplyEventTarget = rng.uniform(18, 42) * (1 + 0.45 * row.crisis_intensity) + 8 * Math.max(0, row.energy_price_impulse);
        } else if (roll < shortageChance + glutChance) {
          oilState.supplyEventYearsLeft = rng.randint(2, 6);
          oilState.supplyEventTarget = -rng.uniform(16, 38) * (1 + 0.20 * Math.max(0, 1 - row.realized_growth_pct));
        }
      }

      function classifyOil(row, oilYoy, commodityYoy, brent, demand, supplyShock, inventoryPressure, energyPressure) {
        if (row.year_index === 0) return "initial";
        if (oilYoy >= 18 && row.headline_inflation_pct >= 3.6 && row.realized_growth_pct <= 1.7) return "stagflationary_energy_squeeze";
        if (supplyShock >= 24 && oilYoy >= 16) return "geopolitical_oil_shock";
        if (supplyShock <= -22 && oilYoy <= -10) return "supply_glut_disinflation";
        if (demand <= 38 && oilYoy <= -14) return "oil_demand_slump";
        if (demand >= 63 && commodityYoy >= 10 && row.global_dollar_index <= 99) return "commodity_supercycle";
        if (oilYoy >= 12 && row.risk_appetite_index >= 58 && row.global_liquidity_index >= 60) return "risk_on_commodity_bid";
        if (row.global_dollar_index >= 106 && oilYoy <= 3) return "strong_dollar_oil_pressure";
        if (energyPressure >= 64 && row.headline_inflation_pct >= 4) return "energy_inflation_pressure";
        if (brent <= 45 && inventoryPressure <= -20) return "oil_glut_disinflation";
        if (row.crisis_intensity >= 0.55 && oilYoy < 0) return "crisis_oil_liquidation";
        return "normal_oil_cycle";
      }

      return rows.map((row) => {
        maybeUpdateSupplyEvent(row);
        const priceDemandDrag = 0.16 * Math.max(0, oilState.brent - 105) + 0.04 * Math.max(0, oilState.oilReturn - 15) + 0.04 * Math.max(0, row.asset_volatility_index - 38);
        const demandTarget = 54 + 4.3 * (row.realized_growth_pct - row.potential_growth_pct) + 1.8 * row.output_gap_pct + 0.18 * (row.risk_appetite_index - 50) + 0.12 * (row.global_liquidity_index - 50) + 0.09 * row.liquidity_impulse_index + 0.045 * row.global_equity_total_return_pct + 3.0 * row.credit_to_oil_demand_impulse - 7 * row.crisis_intensity - 0.010 * Math.max(0, row.global_high_yield_spread_bps - 500) - 0.10 * Math.max(0, row.financial_stress_index - 40) - priceDemandDrag + rng.gauss(0, 2.0);
        const demand = clamp(smooth(oilState.demand, demandTarget, 0.32), 0, 100);
        const supplyTarget = oilState.supplyEventTarget + 7 * row.energy_price_impulse + rng.gauss(0, 2.2);
        const supplyShock = clamp(smooth(oilState.supplyShock, supplyTarget, 0.36), -55, 70);
        const inventoryTarget = 0.58 * (demand - 50) + 0.62 * supplyShock - 0.16 * (oilState.brent - 82) - 0.14 * Math.max(0, oilState.oilReturn);
        const inventoryPressure = clamp(smooth(oilState.inventoryPressure, inventoryTarget, 0.30), -65, 80);
        const financialPressure = clamp(
          -0.30 * (row.global_dollar_index - 100)
          - 0.42 * row.dollar_momentum_index
          + 0.16 * (row.global_liquidity_index - 50)
          + 0.13 * (row.risk_appetite_index - 50)
          - 3.2 * Math.max(0, row.global_financial_conditions_index)
          + 5.5 * row.dollar_to_oil_pressure_impulse
          + 0.045 * row.global_equity_total_return_pct
          - 0.020 * Math.max(0, row.global_high_yield_spread_bps - 500),
          -28,
          28,
        );
        const priceLevelGravity = -0.12 * Math.max(0, oilState.brent - 135) + 0.20 * Math.max(0, 62 - oilState.brent);
        const oilReturnTarget = 1.2 + 0.35 * row.headline_inflation_pct + 0.44 * (demand - 50) + 0.82 * supplyShock + 0.28 * inventoryPressure + 0.38 * financialPressure + 10 * row.energy_price_impulse + priceLevelGravity + rng.gauss(0, 5.5);
        const oilYoy = row.year_index === 0 ? 0 : clamp(smooth(oilState.oilReturn, oilReturnTarget, 0.38), -42, 85);
        const brent = row.year_index === 0 ? 82 : Math.max(18, oilState.brent * (1 + oilYoy / 100));
        const oilIndex = row.year_index === 0 ? 100 : Math.max(22, oilState.oilIndex * (1 + oilYoy / 100));
        const commodityReturnTarget = 0.46 * oilYoy + 0.20 * (demand - 50) + 0.17 * financialPressure - 0.18 * (row.global_dollar_index - 100) + 0.06 * row.global_equity_total_return_pct + rng.gauss(0, 3.0);
        const commodityYoy = row.year_index === 0 ? 0 : clamp(smooth(oilState.commodityReturn, commodityReturnTarget, 0.32), -38, 60);
        const commodityIndex = row.year_index === 0 ? 100 : compoundIndexWithSoftDrag(oilState.commodityIndex, commodityYoy, 28, 260, 0.75);
        const energyPressureTarget = 50 + 0.38 * (brent - 82) + 0.52 * oilYoy + 0.28 * inventoryPressure + 0.18 * supplyShock;
        const energyPressure = clamp(smooth(oilState.energyPressure, energyPressureTarget, 0.40), 0, 100);
        const regime = classifyOil(row, oilYoy, commodityYoy, brent, demand, supplyShock, inventoryPressure, energyPressure);
        const headlineImpulse = clamp(0.018 * oilYoy + 0.010 * (energyPressure - 50) + 0.004 * supplyShock, -1.4, 2.4);
        const gdpDrag = clamp(-0.020 * Math.max(0, oilYoy - 15) - 0.018 * Math.max(0, brent - 110) - 0.008 * Math.max(0, energyPressure - 65) + 0.014 * Math.max(0, -oilYoy - 10), -2.2, 0.8);
        const creditStress = clamp(0.012 * Math.max(0, oilYoy - 15) + 0.012 * Math.max(0, energyPressure - 65) + 0.006 * Math.max(0, brent - 110) - 0.006 * Math.max(0, -oilYoy - 15), -0.8, 1.8);
        const policyPressure = clamp(0.016 * Math.max(0, oilYoy) + 0.010 * Math.max(0, energyPressure - 55) - 0.010 * Math.max(0, -oilYoy - 12), -1, 1.8);
        const termsOfTrade = clamp(0.018 * commodityYoy - 0.010 * (row.global_dollar_index - 100) + 0.004 * (demand - 50), -1.2, 1.2);

        const next = roundRow({
          ...row,
          oil_commodity_param_version: "global-oil-commodity-layer-v0.1-js",
          oil_commodity_interface_version: "oil-commodity-feedback-interface-v0.1",
          brent_oil_price_usd: brent,
          global_oil_price_index: oilIndex,
          oil_yoy_change_pct: oilYoy,
          broad_commodity_index: commodityIndex,
          commodity_yoy_change_pct: commodityYoy,
          oil_demand_pressure_index: demand,
          oil_supply_shock_index: supplyShock,
          oil_inventory_pressure_index: inventoryPressure,
          energy_cost_pressure_index: energyPressure,
          oil_financial_pressure_index: financialPressure,
          oil_regime: regime,
          oil_to_headline_inflation_impulse: headlineImpulse,
          oil_to_gdp_drag_placeholder: gdpDrag,
          oil_to_credit_stress_impulse: creditStress,
          oil_to_policy_pressure_impulse: policyPressure,
          commodity_to_terms_of_trade_impulse: termsOfTrade,
        });

        oilState.brent = brent;
        oilState.oilIndex = oilIndex;
        oilState.commodityIndex = commodityIndex;
        oilState.oilReturn = oilYoy;
        oilState.commodityReturn = commodityYoy;
        oilState.demand = demand;
        oilState.supplyShock = supplyShock;
        oilState.inventoryPressure = inventoryPressure;
        oilState.energyPressure = energyPressure;
        return next;
      });
    }

    function deriveDynamicFeedbackPath(rows) {
      const feedback = {};
      let previousGrowth = 0;
      let previousStress = 0;
      let previousInflation = 0;
      let previousPolicy = 0;
      const lastIndex = rows[rows.length - 1]?.year_index ?? 0;

      rows.forEach((row) => {
        if (row.year_index <= 0) return;
        const targetIndex = row.year_index + 1;
        if (targetIndex > lastIndex) return;
        const creditDrag = row.credit_to_gdp_drag_placeholder || 0;
        const dollarDrag = row.dollar_to_gdp_drag_placeholder || 0;
        const policyDrag = row.policy_to_gdp_drag_placeholder || 0;
        const inflationDrag = row.inflation_to_gdp_drag_placeholder || 0;
        const yieldDrag = row.yield_curve_to_gdp_drag_placeholder || 0;
        const oilDrag = row.oil_to_gdp_drag_placeholder || 0;
        const wealth = row.asset_to_gdp_wealth_impulse || 0;
        const laggedSupport = row.gdp_lagged_support || 0;
        const creditImpairment = row.credit_impairment_stock_index || 0;
        const growthRaw = 0.34 * creditDrag + 0.30 * dollarDrag + 0.24 * policyDrag + 0.22 * inflationDrag + 0.44 * oilDrag + 0.34 * wealth + 0.24 * yieldDrag + 0.18 * laggedSupport + 0.008 * ((row.risk_appetite_index || 50) - 50) + 0.008 * ((row.global_liquidity_index || 55) - 55) + 0.006 * ((row.credit_availability_index || 58) - 58) - 0.005 * creditImpairment;
        const growth = clamp(smooth(previousGrowth, growthRaw, 0.42), -1.15, 0.85);

        const hy = row.global_high_yield_spread_bps || 420;
        const spreadChange = row.credit_spread_change_bps || 0;
        const stressRaw = 0.010 * Math.max(0, hy - 520) + 0.030 * Math.max(0, spreadChange) + 1.30 * Math.max(0, row.oil_to_credit_stress_impulse || 0) + 1.15 * Math.max(0, row.asset_to_policy_financial_conditions_impulse || 0) + 0.90 * Math.max(0, row.dollar_to_credit_tightening_impulse || 0) + 0.14 * Math.max(0, row.credit_convexity_pressure_index || 0) + 0.055 * creditImpairment + 0.10 * Math.max(0, (row.bank_balance_sheet_stress_index || 0) - 55) + 0.12 * Math.max(0, 45 - (row.bank_lending_sentiment_index || 55)) - 0.70 * Math.max(0, row.liquidity_to_credit_easing_impulse || 0) - 0.70 * Math.max(0, row.asset_to_credit_risk_appetite_impulse || 0);
        const stress = clamp(smooth(previousStress, stressRaw, 0.38), -8, 16);
        const gap = clamp(0.72 * growth - 0.018 * Math.max(0, hy - 650) - 0.014 * Math.max(0, 45 - (row.bank_lending_sentiment_index || 55)) - 0.006 * creditImpairment + 0.020 * ((row.risk_appetite_index || 50) - 50), -2.2, 1.4);
        const inflationRaw = 0.58 * (row.oil_to_headline_inflation_impulse || 0) + 0.34 * (row.dollar_to_import_inflation_impulse || 0) + 0.24 * (row.asset_to_inflation_wealth_demand_impulse || 0) + 0.30 * (row.policy_to_inflation_lagged_impulse || 0) + 0.28 * (row.credit_to_inflation_demand_drag_placeholder || 0);
        const inflation = clamp(smooth(previousInflation, inflationRaw, 0.40), -1, 1.35);
        const policyRaw = 0.42 * (row.oil_to_policy_pressure_impulse || 0) + 0.36 * (row.inflation_to_policy_rate_impulse || 0) + 0.20 * (row.asset_to_policy_financial_conditions_impulse || 0) - 0.36 * (row.credit_to_policy_easing_pressure || 0);
        const policy = clamp(smooth(previousPolicy, policyRaw, 0.36), -1, 1.25);
        const intensity = clamp(24 * Math.abs(growth) + 2 * Math.max(0, stress) + 18 * Math.abs(inflation) + 18 * Math.abs(policy), 0, 100);
        feedback[targetIndex] = {
          feedback_growth_impulse_pct: growth,
          feedback_output_gap_impulse_pct: gap,
          feedback_financial_stress_impulse: stress,
          feedback_inflation_impulse_pct: inflation,
          feedback_policy_impulse_pct: policy,
          feedback_source: `lagged_macro_feedback_from_year_${row.year}`,
          macro_feedback_intensity_index: intensity,
          macro_feedback_growth_raw_pct: growthRaw,
          macro_feedback_stress_raw: stressRaw,
          macro_feedback_inflation_raw_pct: inflationRaw,
          macro_feedback_policy_raw_pct: policyRaw,
        };
        previousGrowth = growth;
        previousStress = stress;
        previousInflation = inflation;
        previousPolicy = policy;
      });
      return feedback;
    }

    const dynamicFeedbackFields = [
      "feedback_growth_impulse_pct",
      "feedback_output_gap_impulse_pct",
      "feedback_financial_stress_impulse",
      "feedback_inflation_impulse_pct",
      "feedback_policy_impulse_pct",
      "macro_feedback_intensity_index",
      "macro_feedback_growth_raw_pct",
      "macro_feedback_stress_raw",
      "macro_feedback_inflation_raw_pct",
      "macro_feedback_policy_raw_pct",
    ];

    const scenarioImpulseFields = [
      "scenario_event_severity",
      "scenario_policy_rate_impulse",
      "scenario_liquidity_impulse",
      "scenario_credit_stress_impulse",
      "scenario_dollar_pressure_impulse",
      "scenario_energy_price_impulse",
      "scenario_gdp_lagged_support",
    ];

    function mergeDynamicFeedbackPaths(base, overlay) {
      const keys = new Set([...Object.keys(base || {}), ...Object.keys(overlay || {})]);
      const merged = {};
      keys.forEach((key) => {
        const baseRow = base?.[key] || {};
        const overlayRow = overlay?.[key] || {};
        const row = { ...baseRow, ...overlayRow };
        dynamicFeedbackFields.forEach((field) => {
          row[field] = Number(baseRow[field] || 0) + Number(overlayRow[field] || 0);
        });
        scenarioImpulseFields.forEach((field) => {
          row[field] = Number(baseRow[field] || 0) + Number(overlayRow[field] || 0);
        });
        const source = [baseRow.feedback_source, overlayRow.feedback_source].filter(Boolean).join(" + ");
        row.feedback_source = source || "none";
        row.scenario_event_type = overlayRow.scenario_event_type || baseRow.scenario_event_type || "";
        row.scenario_event_phase = overlayRow.scenario_event_phase || baseRow.scenario_event_phase || "";
        merged[key] = row;
      });
      return merged;
    }

    function blendDynamicFeedbackPaths(previous, current, relaxation = 0.25) {
      const keys = new Set([...Object.keys(previous), ...Object.keys(current)]);
      const blended = {};
      keys.forEach((key) => {
        const oldRow = previous[key] || {};
        const newRow = current[key] || {};
        const row = {};
        dynamicFeedbackFields.forEach((field) => {
          row[field] = (oldRow[field] || 0) * (1 - relaxation) + (newRow[field] || 0) * relaxation;
        });
        row.feedback_source = newRow.feedback_source || oldRow.feedback_source || "lagged_macro_feedback";
        blended[key] = row;
      });
      return blended;
    }

    function compareDynamicPasses(previous, current) {
      const previousByIndex = new Map(previous.map((row) => [row.year_index, row]));
      const pairs = current
        .filter((row) => row.year_index > 0 && previousByIndex.has(row.year_index))
        .map((row) => [previousByIndex.get(row.year_index), row]);
      const maxAbs = (field) => Math.max(0, ...pairs.map(([prev, row]) => Math.abs((row[field] || 0) - (prev[field] || 0))));
      const maxGrowth = maxAbs("realized_growth_pct");
      const maxInflation = maxAbs("headline_inflation_pct");
      const maxPolicy = maxAbs("global_policy_rate_pct");
      const maxHy = maxAbs("global_high_yield_spread_bps");
      const maxOil = maxAbs("brent_oil_price_usd");
      const deltaIndex = 22 * maxGrowth + 18 * maxInflation + 16 * maxPolicy + maxHy / 8 + maxOil / 6;
      return {
        pass_delta_index: deltaIndex,
        pass_converged: deltaIndex <= 75 && maxGrowth <= 0.65 && maxInflation <= 0.75 && maxPolicy <= 1.15 && maxHy <= 300 && maxOil <= 135,
      };
    }

    function summarizeDynamicConvergence(passRows) {
      const diagnostics = [];
      for (let i = 1; i < passRows.length; i += 1) {
        diagnostics.push(compareDynamicPasses(passRows[i - 1], passRows[i]));
      }
      const last = diagnostics[diagnostics.length - 1] || { pass_delta_index: 0, pass_converged: true };
      return {
        converged: last.pass_converged,
        last_pass_delta_index: last.pass_delta_index,
        max_pass_delta_index: Math.max(0, ...diagnostics.map((item) => item.pass_delta_index)),
      };
    }

    function branchProbability(score) {
      return Number(clamp(5 + 0.75 * score, 10, 85).toFixed(1));
    }

    function addBranchRisk(candidates, item) {
      if (item.score < item.threshold) return;
      candidates.push({
        id: item.id,
        label: item.label,
        probability_pct: branchProbability(item.score),
        severity_index: Number(clamp(item.score, 0, 100).toFixed(1)),
        horizon_years: item.horizonYears,
        impact_years: item.impactYears,
        tail_years: item.tailYears,
        cooldown_years: item.cooldownYears,
        summary: item.summary,
        evidence: item.evidence,
      });
    }

    function detectBranchRisks(rows, index) {
      const row = rows[index];
      if (!row || Number(row.year_index) <= 0) return [];
      const prev = rows[Math.max(0, index - 1)] || row;
      const recent = rows.slice(Math.max(0, index - 3), index + 1);
      const growth = numericValue(row, "realized_growth_pct");
      const gap = numericValue(row, "output_gap_pct");
      const headline = numericValue(row, "headline_inflation_pct", 2.35);
      const prevHeadline = numericValue(prev, "headline_inflation_pct", headline);
      const core = numericValue(row, "core_inflation_pct", 2.2);
      const expectation = numericValue(row, "inflation_expectation_pct", 2.35);
      const policyChange = numericValue(row, "policy_rate_change_pct");
      const realPolicy = numericValue(row, "real_policy_rate_pct");
      const neutralPolicy = numericValue(row, "neutral_policy_rate_pct", 3.25);
      const hikePressure = numericValue(row, "rate_hike_pressure");
      const cutPressure = numericValue(row, "rate_cut_pressure");
      const qe = numericValue(row, "qe_liquidity_index");
      const tenYear = numericValue(row, "global_10y_yield_pct");
      const prevTenYear = numericValue(prev, "global_10y_yield_pct", tenYear);
      const termSpread = numericValue(row, "term_spread_10y_2y_pct");
      const termPremium = numericValue(row, "term_premium_pct");
      const dollar = numericValue(row, "global_dollar_index", 100);
      const dollarYoy = numericValue(row, "dollar_yoy_change_pct");
      const liquidity = numericValue(row, "global_liquidity_index", 55);
      const liquidityImpulse = numericValue(row, "liquidity_impulse_index");
      const fundingStress = numericValue(row, "dollar_funding_stress_index");
      const emStress = numericValue(row, "em_stress_index");
      const fci = numericValue(row, "global_financial_conditions_index");
      const riskAppetite = numericValue(row, "risk_appetite_index", 50);
      const hy = numericValue(row, "global_high_yield_spread_bps", 420);
      const prevHy = numericValue(prev, "global_high_yield_spread_bps", hy);
      const spreadChange = numericValue(row, "credit_spread_change_bps");
      const availability = numericValue(row, "credit_availability_index", 58);
      const bankSentiment = numericValue(row, "bank_lending_sentiment_index", 54);
      const impairment = numericValue(row, "credit_impairment_stock_index");
      const refinancing = numericValue(row, "corporate_refinancing_pressure_index");
      const defaultRisk = numericValue(row, "default_risk_index");
      const equityReturn = numericValue(row, "global_equity_total_return_pct");
      const epsGrowth = numericValue(row, "global_equity_eps_growth_pct");
      const pe = numericValue(row, "global_equity_valuation_pe");
      const prevPe = numericValue(prev, "global_equity_valuation_pe", pe);
      const sovereignReturn = numericValue(row, "global_sovereign_bond_total_return_pct");
      const brent = numericValue(row, "brent_oil_price_usd");
      const oilYoy = numericValue(row, "oil_yoy_change_pct");
      const oilDemand = numericValue(row, "oil_demand_pressure_index", 50);
      const oilSupply = numericValue(row, "oil_supply_shock_index");
      const energyPressure = numericValue(row, "energy_cost_pressure_index");
      const crisisRecent = recent.some((item) => (
        numericValue(item, "realized_growth_pct") < 0
        || numericValue(item, "output_gap_pct") < -3.5
        || numericValue(item, "global_high_yield_spread_bps", 420) > 700
        || numericValue(item, "credit_impairment_stock_index") > 45
      ));

      const candidates = [];
      let score = 0;

      score = 0;
      score += crisisRecent ? 18 : 0;
      score += growth > 0.8 ? 14 : 0;
      score += hy < prevHy - 20 ? 12 : 0;
      score += equityReturn > 3 ? 10 : 0;
      score += gap < -2 ? 14 : 0;
      score += impairment > 35 ? 14 : impairment > 20 ? 7 : 0;
      score += bankSentiment < 52 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "false_dawn",
        label: "虚假黎明",
        score,
        threshold: 64,
        horizonYears: 3,
        impactYears: 3,
        tailYears: 4,
        cooldownYears: 3,
        summary: "表面复苏已经出现，但信用疤痕和负产出缺口仍在，后面几年可能二次探底。",
        evidence: [`GDP ${fmtPct(growth)}`, `HY ${fmtBps(hy)}`, `信用疤痕 ${fmtIndex(impairment)}`, `产出缺口 ${fmtPct(gap)}`],
      });

      score = 0;
      score += headline < 2.5 ? 18 : 0;
      score += gap < 0 ? 16 : 0;
      score += policyChange > 0.15 ? 18 : policyChange > 0 ? 8 : 0;
      score += realPolicy > 0.5 ? 12 : 0;
      score += cutPressure > hikePressure ? 10 : 0;
      score += termSpread < -0.35 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "policy_mistake_tightening",
        label: "政策失误：过早收紧",
        score,
        threshold: 58,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 3,
        cooldownYears: 2,
        summary: "通胀不高且产出缺口为负时仍继续收紧，软着陆路径有转向衰退的风险。",
        evidence: [`Headline ${fmtLevelPct(headline)}`, `产出缺口 ${fmtPct(gap)}`, `政策变化 ${fmtPct(policyChange)}`, `实际政策 ${fmtLevelPct(realPolicy)}`],
      });

      score = 0;
      score += headline > 3.5 ? 18 : headline > 3 ? 9 : 0;
      score += core > 3 ? 16 : core > 2.7 ? 8 : 0;
      score += expectation > 3 ? 12 : 0;
      score += policyChange <= 0.05 ? 14 : 0;
      score += realPolicy < neutralPolicy - 0.5 ? 10 : 0;
      score += liquidity > 60 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "policy_behind_curve",
        label: "政策失误：落后曲线",
        score,
        threshold: 58,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 3,
        cooldownYears: 2,
        summary: "通胀和预期已经升温，但政策反应偏慢，未来可能走向通胀再加速或滞胀。",
        evidence: [`Headline ${fmtLevelPct(headline)}`, `Core ${fmtLevelPct(core)}`, `政策变化 ${fmtPct(policyChange)}`, `预期 ${fmtLevelPct(expectation)}`],
      });

      score = 0;
      score += hy > 720 ? 18 : hy > 620 ? 10 : 0;
      score += refinancing > 65 ? 16 : refinancing > 55 ? 8 : 0;
      score += availability < 45 ? 14 : availability < 55 ? 7 : 0;
      score += defaultRisk > 60 ? 12 : 0;
      score += spreadChange > 45 ? 10 : 0;
      score += impairment > 35 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "credit_accident",
        label: "信用事故",
        score,
        threshold: 58,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 5,
        cooldownYears: 3,
        summary: "高收益利差、再融资压力和信用可得性同时恶化，可能触发信用市场二次冻结。",
        evidence: [`HY ${fmtBps(hy)}`, `再融资 ${fmtIndex(refinancing)}`, `信用可得性 ${fmtIndex(availability)}`, `违约风险 ${fmtIndex(defaultRisk)}`],
      });

      score = 0;
      score += qe > 35 ? 14 : 0;
      score += liquidity > 58 ? 12 : 0;
      score += bankSentiment < 45 ? 18 : bankSentiment < 52 ? 9 : 0;
      score += availability < 50 ? 16 : availability < 58 ? 8 : 0;
      score += impairment > 30 ? 12 : 0;
      addBranchRisk(candidates, {
        id: "bank_lending_trap",
        label: "银行惜贷循环",
        score,
        threshold: 58,
        horizonYears: 3,
        impactYears: 3,
        tailYears: 5,
        cooldownYears: 3,
        summary: "流动性并不稀缺，但银行仍不愿扩张贷款，政策传导可能卡在金融系统内部。",
        evidence: [`QE ${fmtIndex(qe)}`, `流动性 ${fmtIndex(liquidity)}`, `银行意愿 ${fmtIndex(bankSentiment)}`, `信用可得性 ${fmtIndex(availability)}`],
      });

      score = 0;
      score += dollar > 108 ? 18 : dollar > 104 ? 9 : 0;
      score += dollarYoy > 4 ? 14 : dollarYoy > 2 ? 7 : 0;
      score += fundingStress > 55 ? 18 : fundingStress > 45 ? 9 : 0;
      score += emStress > 55 ? 14 : emStress > 45 ? 7 : 0;
      score += liquidity < 48 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "dollar_squeeze_escalation",
        label: "美元挤兑升级",
        score,
        threshold: 58,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 2,
        cooldownYears: 2,
        summary: "美元走强和融资压力可能进一步抽紧全球流动性，外部部门和风险资产更脆弱。",
        evidence: [`美元 ${fmtIndex(dollar)}`, `美元YoY ${fmtPct(dollarYoy)}`, `融资压力 ${fmtIndex(fundingStress)}`, `EM压力 ${fmtIndex(emStress)}`],
      });

      score = 0;
      score += brent > 115 ? 16 : brent > 100 ? 8 : 0;
      score += oilYoy > 22 ? 16 : oilYoy > 12 ? 8 : 0;
      score += energyPressure > 68 ? 14 : energyPressure > 58 ? 7 : 0;
      score += oilSupply > 25 ? 12 : 0;
      score += headline > 3.2 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "energy_shock_escalation",
        label: "能源冲击升级",
        score,
        threshold: 56,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 3,
        cooldownYears: 2,
        summary: "能源价格已经在高位，若供给冲击延续，增长和通胀会同时受到压力。",
        evidence: [`Brent ${fmtOil(brent)}`, `油价YoY ${fmtPct(oilYoy)}`, `能源压力 ${fmtIndex(energyPressure)}`, `供给冲击 ${fmtIndex(oilSupply)}`],
      });

      score = 0;
      score += tenYear - prevTenYear > 0.55 ? 18 : tenYear - prevTenYear > 0.3 ? 9 : 0;
      score += termPremium > 1.1 ? 14 : termPremium > 0.9 ? 7 : 0;
      score += sovereignReturn < -5 ? 18 : sovereignReturn < -3 ? 9 : 0;
      score += headline > 3.2 ? 10 : 0;
      score += fci > 1 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "bond_market_accident",
        label: "债券市场失控",
        score,
        threshold: 56,
        horizonYears: 1,
        impactYears: 1,
        tailYears: 2,
        cooldownYears: 1,
        summary: "长端利率或期限溢价快速上行，可能引发股债同跌和政策空间收缩。",
        evidence: [`10Y变化 ${fmtPct(tenYear - prevTenYear)}`, `期限溢价 ${fmtLevelPct(termPremium)}`, `主权债 ${fmtPct(sovereignReturn)}`, `FCI ${fmtIndex(fci)}`],
      });

      score = 0;
      score += growth >= 1.4 && growth <= 3.3 ? 16 : 0;
      score += gap >= -1.5 && gap <= 0.8 ? 14 : 0;
      score += headline < prevHeadline && headline >= 1.6 && headline <= 3 ? 12 : 0;
      score += hy < 560 ? 12 : 0;
      score += bankSentiment > 52 ? 10 : 0;
      score += impairment < 25 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "soft_landing_success",
        label: "软着陆成功",
        score,
        threshold: 62,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 2,
        cooldownYears: 2,
        summary: "通胀降温且增长没有破位，如果信用保持稳定，路径可能转入温和扩张。",
        evidence: [`GDP ${fmtPct(growth)}`, `Headline ${fmtLevelPct(headline)}`, `HY ${fmtBps(hy)}`, `信用疤痕 ${fmtIndex(impairment)}`],
      });

      score = 0;
      score += liquidity > 64 ? 16 : liquidity > 58 ? 8 : 0;
      score += qe > 35 ? 12 : 0;
      score += equityReturn > 8 ? 16 : equityReturn > 5 ? 8 : 0;
      score += pe - prevPe > 0.5 || pe > 24 ? 12 : 0;
      score += growth < 2.2 || epsGrowth < 1.5 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "liquidity_bubble",
        label: "流动性牛市脱实向虚",
        score,
        threshold: 58,
        horizonYears: 3,
        impactYears: 2,
        tailYears: 3,
        cooldownYears: 3,
        summary: "资产上涨主要由流动性和估值驱动，若盈利跟不上，后续泡沫脆弱度会上升。",
        evidence: [`流动性 ${fmtIndex(liquidity)}`, `QE ${fmtIndex(qe)}`, `股票 ${fmtPct(equityReturn)}`, `EPS ${fmtPct(epsGrowth)}`],
      });

      score = 0;
      score += refinancing > 65 ? 18 : refinancing > 55 ? 9 : 0;
      score += hy > 650 ? 14 : hy > 560 ? 7 : 0;
      score += availability < 48 ? 14 : 0;
      score += realPolicy > 1 ? 10 : 0;
      score += impairment > 30 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "refinancing_wall",
        label: "再融资墙",
        score,
        threshold: 56,
        horizonYears: 3,
        impactYears: 3,
        tailYears: 5,
        cooldownYears: 3,
        summary: "企业到期压力和高融资成本叠加，可能延长信用拖累和盈利修复时间。",
        evidence: [`再融资 ${fmtIndex(refinancing)}`, `HY ${fmtBps(hy)}`, `信用可得性 ${fmtIndex(availability)}`, `实际政策 ${fmtLevelPct(realPolicy)}`],
      });

      score = 0;
      score += headline < prevHeadline - 0.35 ? 14 : 0;
      score += oilYoy < -10 ? 14 : oilYoy < -5 ? 7 : 0;
      score += growth < 1.2 ? 14 : 0;
      score += gap < -2 ? 12 : 0;
      score += oilDemand < 45 ? 10 : 0;
      addBranchRisk(candidates, {
        id: "demand_destruction_disinflation",
        label: "需求破坏式降通胀",
        score,
        threshold: 54,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 3,
        cooldownYears: 2,
        summary: "通胀回落可能来自需求坍缩而非健康降温，未来增长仍有下行分岔。",
        evidence: [`Headline变化 ${fmtPct(headline - prevHeadline)}`, `油价YoY ${fmtPct(oilYoy)}`, `GDP ${fmtPct(growth)}`, `需求压力 ${fmtIndex(oilDemand)}`],
      });

      score = 0;
      score += growth < 1.2 ? 16 : 0;
      score += gap < -1.5 ? 14 : 0;
      score += headline > 3.8 ? 18 : headline > 3.2 ? 9 : 0;
      score += core > 3 ? 14 : 0;
      score += brent > 100 ? 10 : 0;
      score += hy > 600 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "stagflation_trap",
        label: "滞胀陷阱",
        score,
        threshold: 58,
        horizonYears: 3,
        impactYears: 3,
        tailYears: 4,
        cooldownYears: 3,
        summary: "低增长和高通胀同时存在，政策反应很容易在稳增长和控通胀之间反复摇摆。",
        evidence: [`GDP ${fmtPct(growth)}`, `产出缺口 ${fmtPct(gap)}`, `Headline ${fmtLevelPct(headline)}`, `Core ${fmtLevelPct(core)}`],
      });

      score = 0;
      score += equityReturn > 10 ? 18 : equityReturn > 7 ? 9 : 0;
      score += riskAppetite > 62 ? 12 : 0;
      score += pe > 25 ? 12 : 0;
      score += epsGrowth < 1 ? 10 : 0;
      score += hy > 520 || fci > 0.5 ? 8 : 0;
      addBranchRisk(candidates, {
        id: "risk_asset_bull_fragility",
        label: "风险资产牛市脆弱化",
        score,
        threshold: 56,
        horizonYears: 2,
        impactYears: 2,
        tailYears: 2,
        cooldownYears: 2,
        summary: "风险资产表现很好，但盈利或信用基础不够扎实，后续对利率和流动性更敏感。",
        evidence: [`股票 ${fmtPct(equityReturn)}`, `风险偏好 ${fmtIndex(riskAppetite)}`, `PE ${fmtIndex(pe)}`, `EPS ${fmtPct(epsGrowth)}`],
      });

      return candidates.sort((a, b) => b.probability_pct - a.probability_pct);
    }

    function normalizeBranchRisk(item) {
      return {
        id: String(item?.id || ""),
        label: String(item?.label || ""),
        probability_pct: Number(item?.probability_pct || 0),
        severity_index: Number(item?.severity_index || 0),
        horizon_years: Number(item?.horizon_years || 0),
        impact_years: Number(item?.impact_years || item?.impactYears || 0),
        tail_years: Number(item?.tail_years || item?.tailYears || 0),
        cooldown_years: Number(item?.cooldown_years || item?.cooldownYears || 0),
        summary: String(item?.summary || ""),
        evidence: Array.isArray(item?.evidence) ? item.evidence.map(String) : [],
      };
    }

    function parseBranchRiskWatchlist(row) {
      const raw = row?.branch_risk_watchlist;
      if (Array.isArray(raw)) return raw.map(normalizeBranchRisk).filter((item) => item.id);
      if (typeof raw !== "string" || !raw.trim()) return [];
      try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed.map(normalizeBranchRisk).filter((item) => item.id) : [];
      } catch (error) {
        return [];
      }
    }

    function branchRisksForRow(rows, index) {
      const fromRow = parseBranchRiskWatchlist(rows[index]);
      if (fromRow.length) return fromRow.slice(0, 4);
      return detectBranchRisks(rows, index).slice(0, 4);
    }

    function annotateDynamicBranchRisks(rows) {
      const suppressedUntil = new Map();
      return rows.map((row, index) => {
        const risks = detectBranchRisks(rows, index).filter((risk) => {
          const until = suppressedUntil.get(risk.id) ?? -1;
          return index > until;
        });
        const primary = risks[0] || {};
        const watchlist = risks.slice(0, 4);
        watchlist.forEach((risk) => {
          suppressedUntil.set(risk.id, index + Number(risk.cooldown_years || risk.horizon_years || 1));
        });
        return roundRow({
          ...row,
          branch_risk_param_version: "global-branch-risk-layer-v0.1-js",
          branch_risk_interface_version: "branch-risk-watchlist-interface-v0.1",
          branch_risk_primary_id: primary.id || "",
          branch_risk_primary_label: primary.label || "",
          branch_risk_primary_probability_pct: primary.probability_pct || 0,
          branch_risk_primary_severity_index: primary.severity_index || 0,
          branch_risk_primary_horizon_years: primary.horizon_years || 0,
          branch_risk_primary_impact_years: primary.impact_years || 0,
          branch_risk_primary_tail_years: primary.tail_years || 0,
          branch_risk_primary_cooldown_years: primary.cooldown_years || 0,
          branch_risk_secondary_ids: JSON.stringify(risks.slice(1, 4).map((item) => item.id)),
          branch_risk_watchlist: JSON.stringify(watchlist),
          branch_risk_evidence: JSON.stringify(primary.evidence || []),
          branch_risk_count: risks.length,
        });
      });
    }

    function annotateDynamicFeedback(rows, feedbackByIndex, convergence, iterations) {
      const annotated = rows.map((row) => {
        const feedback = feedbackByIndex[row.year_index] || {};
        return roundRow({
          ...row,
          macro_feedback_param_version: "global-macro-feedback-calibration-v0.1-js",
          macro_feedback_interface_version: "macro-feedback-interface-v0.1",
          macro_feedback_iteration: 1,
          macro_feedback_intensity_index: feedback.macro_feedback_intensity_index || 0,
          macro_feedback_growth_raw_pct: feedback.macro_feedback_growth_raw_pct || 0,
          macro_feedback_stress_raw: feedback.macro_feedback_stress_raw || 0,
          macro_feedback_inflation_raw_pct: feedback.macro_feedback_inflation_raw_pct || 0,
          macro_feedback_policy_raw_pct: feedback.macro_feedback_policy_raw_pct || 0,
          macro_feedback_iterations_requested: iterations,
          macro_feedback_converged: String(Boolean(convergence.converged)),
          macro_feedback_last_pass_delta_index: convergence.last_pass_delta_index || 0,
          macro_feedback_max_pass_delta_index: convergence.max_pass_delta_index || 0,
          macro_feedback_note: feedback.feedback_source || "none",
        });
      });
      return annotateDynamicBranchRisks(annotated);
    }

    const branchScenarioProfiles = {
      false_dawn: {
        growth: -0.85, gap: -1.10, stress: 7.0, inflation: -0.15, policy: -0.20,
        policyRate: -0.10, liquidity: 0.15, creditStress: 0.75, dollar: 0.20, energy: -0.10, support: -0.35,
      },
      policy_mistake_tightening: {
        growth: -0.65, gap: -0.90, stress: 5.0, inflation: -0.20, policy: 0.45,
        policyRate: 0.50, liquidity: -0.30, creditStress: 0.45, dollar: 0.25, energy: -0.05, support: -0.25,
      },
      policy_behind_curve: {
        growth: -0.25, gap: -0.25, stress: 3.2, inflation: 0.75, policy: 0.65,
        policyRate: 0.45, liquidity: -0.10, creditStress: 0.25, dollar: 0.10, energy: 0.20, support: -0.10,
      },
      credit_accident: {
        growth: -1.00, gap: -1.50, stress: 12.0, inflation: -0.35, policy: -0.35,
        policyRate: -0.20, liquidity: 0.25, creditStress: 1.20, dollar: 0.45, energy: -0.15, support: -0.45,
      },
      bank_lending_trap: {
        growth: -0.70, gap: -1.05, stress: 6.8, inflation: -0.25, policy: -0.30,
        policyRate: -0.15, liquidity: 0.35, creditStress: 0.78, dollar: 0.20, energy: -0.10, support: -0.35,
      },
      dollar_squeeze_escalation: {
        growth: -0.55, gap: -0.75, stress: 7.6, inflation: -0.12, policy: -0.10,
        policyRate: 0.05, liquidity: -0.35, creditStress: 0.70, dollar: 0.95, energy: -0.18, support: -0.28,
      },
      energy_shock_escalation: {
        growth: -0.45, gap: -0.55, stress: 4.4, inflation: 0.85, policy: 0.55,
        policyRate: 0.35, liquidity: -0.10, creditStress: 0.35, dollar: 0.10, energy: 1.10, support: -0.25,
      },
      bond_market_accident: {
        growth: -0.55, gap: -0.75, stress: 8.0, inflation: 0.20, policy: 0.35,
        policyRate: 0.35, liquidity: -0.30, creditStress: 0.45, dollar: 0.25, energy: 0.05, support: -0.30,
      },
      soft_landing_success: {
        growth: 0.35, gap: 0.45, stress: -3.2, inflation: -0.20, policy: -0.15,
        policyRate: -0.10, liquidity: 0.15, creditStress: -0.35, dollar: -0.10, energy: -0.05, support: 0.22,
      },
      liquidity_bubble: {
        growth: 0.25, gap: 0.25, stress: -1.8, inflation: 0.15, policy: 0.15,
        policyRate: 0.05, liquidity: 0.65, creditStress: -0.25, dollar: -0.20, energy: 0.08, support: 0.15,
      },
      refinancing_wall: {
        growth: -0.65, gap: -0.85, stress: 8.0, inflation: -0.20, policy: -0.20,
        policyRate: -0.10, liquidity: 0.15, creditStress: 0.90, dollar: 0.25, energy: -0.12, support: -0.35,
      },
      demand_destruction_disinflation: {
        growth: -0.75, gap: -1.00, stress: 5.2, inflation: -0.65, policy: -0.40,
        policyRate: -0.20, liquidity: 0.20, creditStress: 0.35, dollar: 0.10, energy: -0.35, support: -0.30,
      },
      stagflation_trap: {
        growth: -0.55, gap: -0.65, stress: 5.4, inflation: 0.75, policy: 0.45,
        policyRate: 0.30, liquidity: -0.15, creditStress: 0.45, dollar: 0.15, energy: 0.55, support: -0.30,
      },
      risk_asset_bull_fragility: {
        growth: 0.12, gap: 0.15, stress: -1.2, inflation: 0.08, policy: 0.08,
        policyRate: 0.02, liquidity: 0.45, creditStress: -0.15, dollar: -0.12, energy: 0.05, support: 0.10,
      },
    };

    const scenarioRatioFields = new Set([
      "global_gdp_trillion_usd",
      "real_gdp_index",
      "potential_gdp_index",
      "yield_curve_reference_10y_bond_total_return_index",
      "global_equity_price_index",
      "global_equity_eps_index",
      "global_sovereign_bond_total_return_index",
      "global_corporate_bond_total_return_index",
      "global_60_40_total_return_index",
      "brent_oil_price_usd",
      "global_oil_price_index",
      "broad_commodity_index",
    ]);

    const scenarioSkipNumericFields = new Set([
      "year_index",
      "year",
      "seed",
      "branch_risk_primary_probability_pct",
      "branch_risk_primary_severity_index",
      "branch_risk_primary_horizon_years",
      "branch_risk_primary_impact_years",
      "branch_risk_primary_tail_years",
      "branch_risk_primary_cooldown_years",
      "branch_risk_count",
    ]);

    function normalizedRiskDurations(risk) {
      return {
        horizon: Math.max(1, Number(risk.horizon_years || 1)),
        impact: Math.max(1, Number(risk.impact_years || risk.horizon_years || 2)),
        tail: Math.max(1, Number(risk.tail_years || 2)),
        cooldown: Math.max(1, Number(risk.cooldown_years || risk.horizon_years || 1)),
      };
    }

    function scenarioShape(offset, impactYears, tailYears) {
      if (offset <= 0) return { phase: "pre", strength: 0 };
      if (offset <= impactYears) {
        const progress = impactYears <= 1 ? 1 : (offset - 1) / (impactYears - 1);
        return { phase: "impact", strength: 0.82 + 0.24 * Math.sin(Math.PI * progress) };
      }
      const tailOffset = offset - impactYears;
      if (tailOffset <= tailYears) {
        return { phase: "tail", strength: 0.52 * (1 - tailOffset / (tailYears + 1)) };
      }
      return { phase: "path_dependency", strength: 0 };
    }

    function buildBranchScenarioEventPath(risk, triggerIndex, maxIndex) {
      const profile = branchScenarioProfiles[risk.id] || branchScenarioProfiles.false_dawn;
      const durations = normalizedRiskDurations(risk);
      const severity = clamp(Number(risk.severity_index || risk.probability_pct || 60) / 72, 0.55, 1.35);
      const eventPath = {};
      const totalYears = durations.impact + durations.tail;
      for (let offset = 1; offset <= totalYears; offset += 1) {
        const targetIndex = triggerIndex + offset;
        if (targetIndex > maxIndex) break;
        const shape = scenarioShape(offset, durations.impact, durations.tail);
        const multiplier = severity * shape.strength;
        eventPath[targetIndex] = {
          feedback_growth_impulse_pct: profile.growth * multiplier,
          feedback_output_gap_impulse_pct: profile.gap * multiplier,
          feedback_financial_stress_impulse: profile.stress * multiplier,
          feedback_inflation_impulse_pct: profile.inflation * multiplier,
          feedback_policy_impulse_pct: profile.policy * multiplier,
          macro_feedback_intensity_index: clamp(34 * Math.abs(multiplier) + 2.2 * Math.max(0, profile.stress * multiplier), 0, 100),
          macro_feedback_growth_raw_pct: profile.growth * multiplier,
          macro_feedback_stress_raw: profile.stress * multiplier,
          macro_feedback_inflation_raw_pct: profile.inflation * multiplier,
          macro_feedback_policy_raw_pct: profile.policy * multiplier,
          scenario_event_severity: clamp(0.55 * multiplier, 0, 1.6),
          scenario_policy_rate_impulse: profile.policyRate * multiplier,
          scenario_liquidity_impulse: profile.liquidity * multiplier,
          scenario_credit_stress_impulse: profile.creditStress * multiplier,
          scenario_dollar_pressure_impulse: profile.dollar * multiplier,
          scenario_energy_price_impulse: profile.energy * multiplier,
          scenario_gdp_lagged_support: profile.support * multiplier,
          scenario_event_type: risk.id,
          scenario_event_phase: shape.phase,
          feedback_source: `${risk.id}_${shape.phase}_from_branch_year_${triggerIndex}`,
        };
      }
      return eventPath;
    }

    function runDynamicMacroWithPersistentFeedback(seed, persistentFeedback = {}, iterations = 3) {
      const passRows = [];
      let macroFeedback = {};
      let combinedFeedback = mergeDynamicFeedbackPaths(macroFeedback, persistentFeedback);
      passRows.push(buildDynamicMacroChain(seed, combinedFeedback));
      for (let i = 0; i < iterations; i += 1) {
        const derived = deriveDynamicFeedbackPath(passRows[passRows.length - 1]);
        macroFeedback = blendDynamicFeedbackPaths(macroFeedback, derived);
        combinedFeedback = mergeDynamicFeedbackPaths(macroFeedback, persistentFeedback);
        passRows.push(buildDynamicMacroChain(seed, combinedFeedback));
      }
      const convergence = summarizeDynamicConvergence(passRows);
      return annotateDynamicFeedback(passRows[passRows.length - 1], combinedFeedback, convergence, iterations);
    }

    function scenarioDeltaValue(key, baseValue, dynamicBaseValue, dynamicScenarioValue) {
      if (!Number.isFinite(baseValue) || !Number.isFinite(dynamicBaseValue) || !Number.isFinite(dynamicScenarioValue)) return baseValue;
      if (scenarioRatioFields.has(key) && Math.abs(dynamicBaseValue) > 1e-9 && dynamicScenarioValue > 0) {
        return baseValue * (dynamicScenarioValue / dynamicBaseValue);
      }
      return baseValue + (dynamicScenarioValue - dynamicBaseValue);
    }

    function applyBranchScenarioDelta(baseRows, dynamicBaseline, dynamicScenario, triggerIndex, risk, eventPath) {
      const baselineByIndex = new Map(dynamicBaseline.map((row) => [row.year_index, row]));
      const scenarioByIndex = new Map(dynamicScenario.map((row) => [row.year_index, row]));
      const durations = normalizedRiskDurations(risk);
      const shifted = baseRows.map((row) => {
        const next = { ...row };
        const offset = row.year_index - triggerIndex;
        if (offset <= 0) {
          next.scenario_phase = "baseline";
          return next;
        }
        const dynamicBaseRow = baselineByIndex.get(row.year_index);
        const dynamicScenarioRow = scenarioByIndex.get(row.year_index);
        if (!dynamicBaseRow || !dynamicScenarioRow) return next;

        for (const key of numFields) {
          if (scenarioSkipNumericFields.has(key)) continue;
          if (!(key in row) || !(key in dynamicBaseRow) || !(key in dynamicScenarioRow)) continue;
          next[key] = scenarioDeltaValue(key, Number(row[key]), Number(dynamicBaseRow[key]), Number(dynamicScenarioRow[key]));
        }
        Object.entries(dynamicScenarioRow).forEach(([key, value]) => {
          if (typeof value === "string" && (key === "regime" || key.endsWith("_regime"))) {
            next[key] = value;
          }
        });
        const phase = eventPath[row.year_index]?.scenario_event_phase || (offset <= durations.impact + durations.tail ? "tail" : "path_dependency");
        next.scenario_phase = phase;
        next.scenario_risk_id = risk.id;
        next.scenario_risk_label = risk.label;
        next.scenario_trigger_index = triggerIndex;
        return roundRow(next);
      });
      return annotateDynamicBranchRisks(shifted).map((row) => ({
        ...row,
        scenario_risk_id: risk.id,
        scenario_risk_label: risk.label,
        scenario_trigger_index: triggerIndex,
      }));
    }

    function buildBranchScenario(rows, selectedIndex, risk) {
      const triggerRow = rows[selectedIndex];
      const maxIndex = rows[rows.length - 1]?.year_index || triggerRow.year_index;
      const durations = normalizedRiskDurations(risk);
      const eventPath = buildBranchScenarioEventPath(risk, triggerRow.year_index, maxIndex);
      const iterations = 3;
      const dynamicBaseline = runDynamicMacroWithPersistentFeedback(state.seed, {}, iterations);
      const dynamicScenario = runDynamicMacroWithPersistentFeedback(state.seed, eventPath, iterations);
      const scenarioRows = applyBranchScenarioDelta(rows, dynamicBaseline, dynamicScenario, triggerRow.year_index, risk, eventPath);
      return {
        id: `${state.seed}-${triggerRow.year}-${risk.id}`,
        seed: state.seed,
        triggerIndex: triggerRow.year_index,
        triggerYear: triggerRow.year,
        risk,
        rows: scenarioRows,
        impactYears: durations.impact,
        tailYears: durations.tail,
        horizonYears: durations.horizon,
        eventPath,
      };
    }

    function activeScenarioRows(rows) {
      if (!state.scenario || state.scenario.seed !== state.seed) return null;
      if (!rows.length) return null;
      return state.scenario.rows;
    }

    function simulateBranchRisk(riskId) {
      const rows = rowsForSeed();
      const index = Math.max(0, Math.min(state.selectedIndex, rows.length - 1));
      const risk = branchRisksForRow(rows, index).find((item) => item.id === riskId);
      if (!risk) return;
      state.scenario = buildBranchScenario(rows, index, risk);
      el.status.textContent = `scenario: ${risk.label} from ${rows[index].year}`;
      render();
    }

    function clearScenario() {
      state.scenario = null;
      el.status.textContent = "scenario cleared; baseline path";
      render();
    }

    function scenarioDeltaSummary(rows) {
      const scenarioRows = activeScenarioRows(rows);
      if (!state.scenario || !scenarioRows) return "";
      const endIndex = Math.min(rows.length - 1, state.scenario.triggerIndex + state.scenario.impactYears + state.scenario.tailYears);
      const baseEnd = rows.find((row) => row.year_index === endIndex) || rows[rows.length - 1];
      const scenarioEnd = scenarioRows.find((row) => row.year_index === endIndex) || scenarioRows[scenarioRows.length - 1];
      const gdpDiff = scenarioEnd && baseEnd ? pctChange(scenarioEnd.global_gdp_trillion_usd, baseEnd.global_gdp_trillion_usd) : 0;
      const hyDiff = scenarioEnd && baseEnd ? (scenarioEnd.global_high_yield_spread_bps || 0) - (baseEnd.global_high_yield_spread_bps || 0) : 0;
      const oilDiff = scenarioEnd && baseEnd ? pctChange(scenarioEnd.brent_oil_price_usd || 0, baseEnd.brent_oil_price_usd || 0) : 0;
      return `窗口末 GDP 水平 ${fmtPct(gdpDiff)}，HY ${hyDiff >= 0 ? "+" : ""}${hyDiff.toFixed(0)}bps，Brent ${fmtPct(oilDiff)}`;
    }

    function buildDynamicMacroChain(seed, feedbackByIndex = {}) {
      return attachDynamicOilCommodities(attachDynamicAssetPrices(attachDynamicCreditSpreads(attachDynamicDollarLiquidity(attachDynamicYieldCurve(attachDynamicPolicy(attachDynamicInflation(seed, simulateDynamicGlobalGdp(seed, feedbackByIndex))))))));
    }

    return Object.freeze({
      branchRisksForRow,
      activeScenarioRows,
      simulateBranchRisk,
      clearScenario,
      scenarioDeltaSummary,
    });
})();
