    function fmtQualityScore(value) {
      return fmt(value, 1);
    }

    function fmtQualityScoreDelta(value) {
      const number = Number(value) || 0;
      return `${number > 0 ? "+" : ""}${fmt(number, 1)} 分`;
    }

    function fmtMultiplier(value) {
      return `${fmt(value, 3)}x`;
    }

    function fmtMaintenanceAge(value) {
      if (value == null || value === "") return "-";
      const number = Number(value);
      if (!Number.isFinite(number)) return "-";
      return `${fmt(Math.max(0, number), 1)} 年`;
    }

    function compactQuarterLabel(quarter) {
      if (!quarter) return "-";
      return `${quarter.year}${quarter.quarter || ""}`;
    }

    function qualitySigmoid(value) {
      return 1 / (1 + Math.exp(-clampNumber(value, -60, 60)));
    }

    function perceivedMaintenanceAgeScore(effectiveAgeYears) {
      if (effectiveAgeYears == null || effectiveAgeYears === "") return null;
      const age = Number(effectiveAgeYears);
      if (!Number.isFinite(age)) return null;
      const model = SERVICE_QUALITY_MAINTENANCE_MODEL.ageScore;
      const softness = Number(model.softnessYears) > 0 ? Number(model.softnessYears) : 8;
      return Number(model.maxScore)
        - Number(model.scoreSpan) * qualitySigmoid((age - Number(model.midpointYears)) / softness);
    }

    function serviceQualityCurrentQuarter() {
      if (!state.operations || !state.operations.quarters.length) return null;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      return state.operations.quarters[currentIndex] || state.operations.quarters[playerStartIndex] || null;
    }

    function projectStartQuarter(project, quarter) {
      return projectHistoryThrough(quarter).find((item) => (
        projectStartedInQuarter(item, project)
        || projectIdsContain(item.projects?.[project.startedIdsKey], project.id)
        || projectIdsContain(item.projects?.[project.activeIdsKey], project.id)
      )) || null;
    }

    function projectCompletionQuarter(project, quarter) {
      return projectHistoryThrough(quarter).find((item) => (
        projectCompletedInQuarter(item, project)
        || projectIdsContain(item.projects?.[project.completedIdsKey], project.id)
      )) || null;
    }

    function renovationLedgerProjectForAction(action) {
      const template = projectTemplateById(action?.templateId);
      const config = action?.eventConfig || {};
      if (!template || template.projectType !== "renovation" || !action?.projectId) return null;
      return {
        id: action.projectId,
        templateId: template.templateId,
        name: template.name,
        airport: template.airport,
        slotId: template.slotId,
        slotRole: template.slotRole,
        facilitySize: config.facility_size || template.facilitySize,
        type: "翻新",
        activeIdsKey: "renovationActiveIds",
        completedIdsKey: "renovationCompletedIds",
        capexKey: "renovationCapex",
        cipKey: "renovationConstructionInProgress",
        originalKey: "renovationAssetOriginal",
        accumulatedDepreciationKey: "renovationAssetAccumulatedDepreciation",
        bookKey: "renovationAssetBookValue",
        depreciationKey: "renovationAssetPeriodDepreciation",
        designLossKey: "renovationDesignCapacityLoss",
        maxLossKey: "renovationMaxCapacityLoss",
      };
    }

    function rebuildLedgerProjectForAction(action) {
      const template = projectTemplateById(action?.templateId);
      const config = action?.eventConfig || {};
      if (!template || template.projectType !== "rebuild" || !action?.projectId) return null;
      return {
        id: action.projectId,
        templateId: template.templateId,
        name: template.name,
        airport: template.airport,
        slotId: template.slotId,
        slotRole: template.slotRole,
        facilitySize: config.target_facility_size || template.targetFacilitySize,
        sourceFacilitySize: config.source_facility_size || template.sourceFacilitySize,
        type: "拆除重建",
        activeIdsKey: "rebuildActiveIds",
        startedIdsKey: "rebuildStartedIds",
        completedIdsKey: "rebuildCompletedIds",
        capexKey: "rebuildCapex",
        demolitionKey: "rebuildDemolitionExpense",
        writeoffKey: "rebuildOldAssetWriteoff",
        cipKey: "rebuildConstructionInProgress",
        originalKey: "rebuildAssetOriginal",
        accumulatedDepreciationKey: "rebuildAssetAccumulatedDepreciation",
        bookKey: "rebuildAssetBookValue",
        depreciationKey: "rebuildAssetPeriodDepreciation",
        designLossKey: "rebuildDesignCapacityLoss",
        maxLossKey: "rebuildMaxCapacityLoss",
        designDeltaKey: "rebuildCompletedDesignCapacityDelta",
        maxDeltaKey: "rebuildCompletedMaxCapacityDelta",
      };
    }

    function demolitionLedgerProjectForAction(action) {
      const template = projectTemplateById(action?.templateId);
      const config = action?.eventConfig || {};
      if (!template || template.projectType !== "demolition" || !action?.projectId) return null;
      return {
        id: action.projectId,
        templateId: template.templateId,
        name: template.name,
        airport: template.airport,
        slotId: template.slotId,
        slotRole: template.slotRole,
        facilitySize: "empty",
        sourceFacilitySize: config.source_facility_size || template.sourceFacilitySize,
        type: "拆除",
        activeIdsKey: "rebuildActiveIds",
        startedIdsKey: "rebuildStartedIds",
        completedIdsKey: "rebuildCompletedIds",
        capexKey: "rebuildCapex",
        demolitionKey: "rebuildDemolitionExpense",
        writeoffKey: "rebuildOldAssetWriteoff",
        cipKey: "rebuildConstructionInProgress",
        originalKey: "rebuildAssetOriginal",
        accumulatedDepreciationKey: "rebuildAssetAccumulatedDepreciation",
        bookKey: "rebuildAssetBookValue",
        depreciationKey: "rebuildAssetPeriodDepreciation",
        designLossKey: "rebuildDesignCapacityLoss",
        maxLossKey: "rebuildMaxCapacityLoss",
        designDeltaKey: "rebuildCompletedDesignCapacityDelta",
        maxDeltaKey: "rebuildCompletedMaxCapacityDelta",
      };
    }

    function constructionLedgerProjectForAction(action) {
      const template = projectTemplateById(action?.templateId);
      const config = action?.eventConfig || {};
      if (!template || template.projectType !== "construction" || !action?.projectId) return null;
      return {
        id: action.projectId,
        templateId: template.templateId,
        name: config.terminal_name || template.name,
        airport: template.airport,
        slotId: template.slotId,
        slotRole: template.slotRole,
        facilitySize: config.target_facility_size || "empty",
        terminalName: config.terminal_name || "",
        type: "新建",
        activeIdsKey: "constructionActiveIds",
        completedIdsKey: "constructionCompletedIds",
        capexKey: "constructionCapex",
        cipKey: "constructionInProgress",
        originalKey: "constructionAssetOriginal",
        accumulatedDepreciationKey: "constructionAssetAccumulatedDepreciation",
        bookKey: "constructionAssetBookValue",
        depreciationKey: "constructionAssetPeriodDepreciation",
      };
    }

    function facilityLedgerProjects() {
      const staticProjects = state.operations?.mode === "simulate_default"
        ? FACILITY_ASSET_LEDGER_PROJECTS.filter((project) => !["翻新", "拆除重建", "新建"].includes(project.type))
        : FACILITY_ASSET_LEDGER_PROJECTS;
      const playerProjects = state.operations?.mode === "simulate_default"
        ? state.playerActions.map(renovationLedgerProjectForAction).filter(Boolean)
        : [];
      const playerRebuilds = state.operations?.mode === "simulate_default"
        ? state.playerActions.map(rebuildLedgerProjectForAction).filter(Boolean)
        : [];
      const playerConstructions = state.operations?.mode === "simulate_default"
        ? state.playerActions.map(constructionLedgerProjectForAction).filter(Boolean)
        : [];
      const playerDemolitions = state.operations?.mode === "simulate_default"
        ? state.playerActions.map(demolitionLedgerProjectForAction).filter(Boolean)
        : [];
      return [...staticProjects, ...playerProjects, ...playerRebuilds, ...playerConstructions, ...playerDemolitions];
    }

    function slotProjects(slotId, type = null) {
      return facilityLedgerProjects().filter((project) => (
        project.slotId === slotId && (!type || project.type === type)
      ));
    }

    function activeSlotProject(slotId, type, quarter) {
      return slotProjects(slotId, type).find((project) => projectActiveNow(project, quarter)) || null;
    }

    function latestCompletedSlotProject(slotId, type, quarter) {
      const completed = slotProjects(slotId, type)
        .map((project) => ({ project, quarter: projectCompletionQuarter(project, quarter) }))
        .filter((item) => item.quarter)
        .sort((a, b) => quarterStartFraction(a.quarter) - quarterStartFraction(b.quarter));
      return completed[completed.length - 1] || null;
    }

    function initialFacilityAssetForSlot(slotId) {
      return FACILITY_LEDGER_INITIAL_ASSETS.find((asset) => asset.slotId === slotId) || null;
    }

    function slotMaintenanceAnchor(slotId, currentQuarter) {
      if (!currentQuarter) return null;
      const targetFraction = quarterStartFraction(currentQuarter);
      const initialAsset = initialFacilityAssetForSlot(slotId);
      let anchorFraction = null;
      let effectiveAgeAtAnchor = 0;
      let source = "-";
      let sourceType = "";

      if (initialAsset && Number(initialAsset.inServiceYear) <= targetFraction) {
        anchorFraction = Number(initialAsset.inServiceYear);
        source = `${initialAsset.inServiceYear} 原始投运`;
        sourceType = "原始投运";
      }

      const completedConstruction = latestCompletedSlotProject(slotId, "新建", currentQuarter);
      const completedRebuild = latestCompletedSlotProject(slotId, "拆除重建", currentQuarter);
      [completedConstruction, completedRebuild].filter(Boolean).forEach((item) => {
        const completionFraction = quarterStartFraction(item.quarter);
        if (completionFraction <= targetFraction && (anchorFraction == null || completionFraction >= anchorFraction)) {
          anchorFraction = completionFraction;
          effectiveAgeAtAnchor = 0;
          source = `${compactQuarterLabel(item.quarter)} ${item.project.type === "新建" ? "新建投运" : "重建投运"}`;
          sourceType = item.project.type;
        }
      });

      if (anchorFraction == null) return null;

      const completedRenovations = slotProjects(slotId, "翻新")
        .map((project) => ({ project, quarter: projectCompletionQuarter(project, currentQuarter) }))
        .filter((item) => item.quarter)
        .map((item) => ({ ...item, fraction: quarterStartFraction(item.quarter) }))
        .filter((item) => item.fraction >= anchorFraction && item.fraction <= targetFraction)
        .sort((a, b) => a.fraction - b.fraction);

      completedRenovations.forEach((item) => {
        const ageAtCompletion = effectiveAgeAtAnchor + Math.max(0, item.fraction - anchorFraction);
        effectiveAgeAtAnchor = Math.max(
          SERVICE_QUALITY_MAINTENANCE_MODEL.renovationMinimumAgeYears,
          ageAtCompletion * SERVICE_QUALITY_MAINTENANCE_MODEL.renovationRetentionRatio,
        );
        anchorFraction = item.fraction;
        source = `${compactQuarterLabel(item.quarter)} 翻新完成`;
        sourceType = "翻新";
      });

      return {
        effectiveAgeYears: effectiveAgeAtAnchor + Math.max(0, targetFraction - anchorFraction),
        source,
        sourceType,
      };
    }

    function currentSlotFacilitySize(slot, currentQuarter) {
      const activeRebuild = activeSlotProject(slot.slotId, "拆除重建", currentQuarter);
      if (activeRebuild) return `${facilitySizeLabel(slot.facilitySize)} -> ${facilitySizeLabel(activeRebuild.facilitySize)}`;
      const completedRebuild = latestCompletedSlotProject(slot.slotId, "拆除重建", currentQuarter);
      if (completedRebuild) return facilitySizeLabel(completedRebuild.project.facilitySize);
      const activeConstruction = activeSlotProject(slot.slotId, "新建", currentQuarter);
      if (activeConstruction) return facilitySizeLabel(activeConstruction.facilitySize);
      const completedConstruction = latestCompletedSlotProject(slot.slotId, "新建", currentQuarter);
      if (completedConstruction) return facilitySizeLabel(completedConstruction.project.facilitySize);
      return facilitySizeLabel(slot.facilitySize);
    }

    function currentSlotDesignCapacity(slot, currentQuarter) {
      const completedRebuild = latestCompletedSlotProject(slot.slotId, "拆除重建", currentQuarter);
      const completedConstruction = latestCompletedSlotProject(slot.slotId, "新建", currentQuarter);
      const size = completedRebuild?.project.facilitySize || completedConstruction?.project.facilitySize || slot.facilitySize;
      return Number(FACILITY_SIZE_DESIGN_CAPACITY[size]) || 0;
    }

    function currentSlotMaxCapacity(slot, currentQuarter) {
      const completedRebuild = latestCompletedSlotProject(slot.slotId, "拆除重建", currentQuarter);
      const completedConstruction = latestCompletedSlotProject(slot.slotId, "新建", currentQuarter);
      const size = completedRebuild?.project.facilitySize || completedConstruction?.project.facilitySize || slot.facilitySize;
      return Number(FACILITY_SIZE_MAX_CAPACITY[size]) || 0;
    }

    function projectTemplateForLedgerProject(project) {
      if (project?.templateId) return projectTemplateById(project.templateId);
      return (state.operations?.projectCatalog || []).find((template) => template.projectId === project?.id) || null;
    }

    function currentSlotAvailableCapacity(slot, currentQuarter) {
      const standardDesign = currentSlotDesignCapacity(slot, currentQuarter);
      const standardMax = currentSlotMaxCapacity(slot, currentQuarter);
      const activeRebuild = activeSlotProject(slot.slotId, "拆除重建", currentQuarter);
      if (activeRebuild) return { standardDesign, standardMax, availableDesign: 0, availableMax: 0 };
      const activeRenovation = activeSlotProject(slot.slotId, "翻新", currentQuarter);
      if (!activeRenovation) return { standardDesign, standardMax, availableDesign: standardDesign, availableMax: standardMax };
      const template = projectTemplateForLedgerProject(activeRenovation);
      const multiplier = Number(renovationEventTerms(template, playerActionForLedgerProject(activeRenovation)).capacityMultiplier);
      const safeMultiplier = Number.isFinite(multiplier) && multiplier > 0
        ? Math.max(0, Math.min(1, multiplier))
        : 0.75;
      return {
        standardDesign,
        standardMax,
        availableDesign: standardDesign * safeMultiplier,
        availableMax: standardMax * safeMultiplier,
      };
    }

    function slotConstructionQualityImpact(slot, currentQuarter) {
      const activeRenovation = activeSlotProject(slot.slotId, "翻新", currentQuarter);
      if (!activeRenovation) return 0;
      const template = projectTemplateForLedgerProject(activeRenovation);
      const score = Number(template?.constructionQualityDisruptionScore);
      return Number.isFinite(score) ? score : -5;
    }

    function slotProjectStatusSummary(slot, currentQuarter) {
      const activeProject = [
        activeSlotProject(slot.slotId, "翻新", currentQuarter),
        activeSlotProject(slot.slotId, "拆除重建", currentQuarter),
        activeSlotProject(slot.slotId, "新建", currentQuarter),
      ].find(Boolean);
      if (activeProject) {
        const template = projectTemplateForLedgerProject(activeProject);
        const startQuarter = projectStartQuarter(activeProject, currentQuarter);
        const action = playerActionForLedgerProject(activeProject);
        const duration = Number(action?.eventConfig?.duration_quarters ?? template?.durationQuarters) || 0;
        const elapsed = startQuarter ? Math.max(1, Number(currentQuarter.index) - Number(startQuarter.index) + 1) : 0;
        const completion = startQuarter && duration > 0
          ? projectQuarterLabel(Number(startQuarter.index) + duration)
          : "-";
        return `${activeProject.type}施工 ${elapsed}/${duration || "-"} 季，预计 ${completion}`;
      }
      const latestCompleted = slotProjects(slot.slotId)
        .map((project) => ({ project, quarter: projectCompletionQuarter(project, currentQuarter) }))
        .filter((item) => item.quarter)
        .sort((left, right) => Number(right.quarter.index) - Number(left.quarter.index))[0];
      return latestCompleted
        ? `最近 ${latestCompleted.project.type}于 ${latestCompleted.quarter.label} 完工`
        : "无在建工程";
    }

    function serviceQualityMaintenanceSlots(currentQuarter) {
      return PROJECT_AFFAIRS_SLOTS.filter((slot) => {
        const hasInitialAsset = Boolean(initialFacilityAssetForSlot(slot.slotId));
        const hasConstruction = slotProjects(slot.slotId, "新建").some((project) => (
          projectStartQuarter(project, currentQuarter) || projectCompletedThrough(project, currentQuarter)
        ));
        return hasInitialAsset || hasConstruction;
      }).map((slot) => ({
        ...slot,
        name: slotDisplayName(slot.slotId, slot.name),
        facilitySize: projectSlotCurrentSize(slot, currentQuarter),
      }));
    }

    function buildServiceQualityMaintenanceRows() {
      const currentQuarter = serviceQualityCurrentQuarter();
      if (!currentQuarter) return [];
      return serviceQualityMaintenanceSlots(currentQuarter).map((slot) => {
        const activeRenovation = activeSlotProject(slot.slotId, "翻新", currentQuarter);
        const activeRebuild = activeSlotProject(slot.slotId, "拆除重建", currentQuarter);
        const activeConstruction = activeSlotProject(slot.slotId, "新建", currentQuarter);
        const anchor = slotMaintenanceAnchor(slot.slotId, currentQuarter);
        let status = "使用中";
        let source = anchor?.source || "-";
        let effectiveAgeYears = anchor?.effectiveAgeYears ?? null;
        if (activeConstruction) {
          status = "施工中";
          source = `${compactQuarterLabel(projectStartQuarter(activeConstruction, currentQuarter))} 新建施工`;
          effectiveAgeYears = null;
        } else if (activeRebuild) {
          status = "施工关闭";
          source = `${compactQuarterLabel(projectStartQuarter(activeRebuild, currentQuarter))} 拆除重建施工`;
          effectiveAgeYears = null;
        } else if (activeRenovation) {
          status = "施工扰动";
          source = `${compactQuarterLabel(projectStartQuarter(activeRenovation, currentQuarter))} 翻新施工`;
        } else if (anchor?.sourceType === "新建" || anchor?.sourceType === "拆除重建") {
          status = "投运使用";
        }
        const ageScore = perceivedMaintenanceAgeScore(effectiveAgeYears);
        const designCapacity = currentSlotDesignCapacity(slot, currentQuarter);
        return {
          name: slot.name,
          airport: slot.airport,
          slotLabel: slotDisplayLabel(slot.slotRole, slot.slotId),
          facilitySize: currentSlotFacilitySize(slot, currentQuarter),
          status,
          effectiveAgeYears,
          source,
          ageScore,
          designCapacity,
          participates: effectiveAgeYears != null
            && Number.isFinite(Number(effectiveAgeYears))
            && !["施工关闭", "施工中"].includes(status),
        };
      });
    }

    function renderServiceQualityMaintenanceStatus(config) {
      const currentQuarter = serviceQualityCurrentQuarter();
      const rows = buildServiceQualityMaintenanceRows();
      el.serviceQualityMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-service-quality-metric") === state.serviceQualityMetric));
      });
      el.serviceQualityMetricTitle.textContent = config.label;
      el.serviceQualityMetricCaption.textContent = currentQuarter
        ? `${currentQuarter.label}；${config.caption}`
        : config.caption;
      el.serviceQualityChartPanel.hidden = true;
      el.serviceQualityMetricTable.hidden = true;
      el.serviceQualityMaintenanceTable.hidden = false;
      el.serviceQualityRangeInput.hidden = true;
      el.serviceQualityTicks.hidden = true;
      el.serviceQualityRangeInput.disabled = true;
      el.serviceQualityRangeInput.min = "0";
      el.serviceQualityRangeInput.max = "0";
      el.serviceQualityRangeInput.value = "0";
      el.serviceQualityWindowLabel.textContent = currentQuarter?.label || "当前季度";
      el.serviceQualityWindowHint.textContent = "随上方运营季度切换";
      if (!state.operations || !currentQuarter) {
        el.serviceQualityMaintenanceCaption.textContent = "暂无运营数据";
        el.serviceQualityMaintenanceRows.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        return;
      }
      el.serviceQualityMaintenanceCaption.textContent = `${currentQuarter.label}；按运营槽位解释维护年龄，内部槽位 ID 不在此处展示`;
      el.serviceQualityMaintenanceRows.innerHTML = rows.length ? rows.map((row) => `
        <tr>
          <td>${escapeHtml(row.name)}</td>
          <td>${escapeHtml(row.airport)}</td>
          <td>${escapeHtml(row.slotLabel)}</td>
          <td>${escapeHtml(row.facilitySize)}</td>
          <td>${escapeHtml(row.status)}</td>
          <td>${escapeHtml(fmtMaintenanceAge(row.effectiveAgeYears))}</td>
          <td>${escapeHtml(row.source)}</td>
          <td>${row.ageScore == null ? "-" : escapeHtml(fmtQualityScoreDelta(row.ageScore))}</td>
        </tr>
      `).join("") : `<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无已启动航站楼</td></tr>`;
    }

    function aggregateServiceQualityPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const weightedAverage = (getter, fallback = 0) => {
        let weighted = 0;
        let weightTotal = 0;
        let simpleTotal = 0;
        let simpleCount = 0;
        quarters.forEach((quarter) => {
          const value = Number(getter(quarter));
          if (!Number.isFinite(value)) return;
          const weight = Math.max(0, Number(quarter.demand?.quarterServed) || 0);
          if (weight > 0) {
            weighted += value * weight;
            weightTotal += weight;
          }
          simpleTotal += value;
          simpleCount += 1;
        });
        if (weightTotal > 0) return weighted / weightTotal;
        if (simpleCount > 0) return simpleTotal / simpleCount;
        return fallback;
      };
      const served = sum((quarter) => quarter.demand.quarterServed);
      const designCapacity = sum((quarter) => quarter.capacity.quarterDesignCapacity);
      const maxCapacity = sum((quarter) => quarter.capacity.quarterMaxCapacity);
      const qualityIndex = weightedAverage((quarter) => quarter.capacity.perceivedQualityIndex, 100);
      const sizeScore = weightedAverage((quarter) => quarter.capacity.perceivedQualitySizeScore, 0);
      const ageScore = weightedAverage((quarter) => quarter.capacity.perceivedQualityAgeScore, 0);
      const capacityScore = weightedAverage((quarter) => quarter.capacity.perceivedQualityCapacityScore, 0);
      const constructionDisruptionScore = weightedAverage(
        (quarter) => quarter.capacity.perceivedQualityConstructionDisruptionScore,
        0,
      );
      return {
        served,
        designCapacity,
        maxCapacity,
        qualityIndex,
        sizeScore,
        ageScore,
        capacityScore,
        constructionDisruptionScore,
        designUtilizationPct: designCapacity ? served / designCapacity * 100 : 0,
        maxUtilizationPct: maxCapacity ? served / maxCapacity * 100 : 0,
        crowdingIndex: weightedAverage((quarter) => quarter.capacity.crowdingIndex, 0),
        foodRetailQualityMultiplier: weightedAverage((quarter) => quarter.operations.foodRetailQualityMultiplier, 1),
        dutyFreeQualityMultiplier: weightedAverage((quarter) => quarter.operations.dutyFreeQualityMultiplier, 1),
        luxuryQualityMultiplier: weightedAverage((quarter) => quarter.operations.luxuryQualityMultiplier, 1),
      };
    }

    function serviceQualityMetricConfig(metric = state.serviceQualityMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
        violet: "#a78bfa",
        cyan: "#38bdf8",
      };
      const configs = {
        qualityIndex: {
          label: "感知质量指数",
          caption: "柱：感知质量指数 / 线：同比变化",
          leftFormat: fmtQualityScore,
          bars: [
            { label: "感知质量指数", color: colors.blue, value: (row) => row.qualityIndex, format: fmtQualityScore },
          ],
          line: {
            label: "同比变化",
            color: colors.amber,
            value: (row) => row.yoyDiff,
            format: fmtQualityScoreDelta,
          },
          valueText: (row) => fmtQualityScore(row.qualityIndex),
          growthHeader: "同比变化",
          growthText: (row) => fmtQualityScoreDelta(row.yoyDiff),
          metricValue: (aggregate) => aggregate.qualityIndex,
        },
        qualityBreakdown: {
          label: "质量拆解",
          caption: "堆叠柱：等级/维护年龄/容量压力/施工扰动分 / 线：感知质量指数",
          leftFormat: fmtQualityScoreDelta,
          rightPad: 76,
          stackedBars: [
            { label: "等级分", color: colors.blue, value: (row) => row.sizeScore, format: fmtQualityScoreDelta },
            { label: "维护年龄分", color: colors.green, value: (row) => row.ageScore, format: fmtQualityScoreDelta },
            { label: "容量压力分", color: colors.amber, value: (row) => row.capacityScore, format: fmtQualityScoreDelta },
            { label: "施工扰动分", color: colors.red, value: (row) => row.constructionDisruptionScore, format: fmtQualityScoreDelta },
          ],
          line: {
            label: "感知质量指数",
            color: colors.cyan,
            value: (row) => row.qualityIndex,
            format: fmtQualityScore,
          },
          valueText: (row) => [
            `等级 ${fmtQualityScoreDelta(row.sizeScore)}`,
            `年龄 ${fmtQualityScoreDelta(row.ageScore)}`,
            `容量 ${fmtQualityScoreDelta(row.capacityScore)}`,
            `施工 ${fmtQualityScoreDelta(row.constructionDisruptionScore)}`,
          ].join(" / "),
          growthHeader: "感知质量指数",
          growthText: (row) => fmtQualityScore(row.qualityIndex),
          metricValue: (aggregate) => aggregate.qualityIndex,
        },
        maintenanceStatus: {
          label: "航站楼维护状况",
          caption: "表：按运营槽位解释状态、等效维护年龄、维护来源和维护年龄分",
          ledgerOnly: true,
          leftFormat: fmtQualityScore,
          bars: [],
          valueText: () => "-",
          growthHeader: "维护年龄分",
          growthText: () => "-",
          metricValue: (aggregate) => aggregate.ageScore,
        },
        capacityComfort: {
          label: "容量舒适度",
          caption: "柱：设计/极限利用率 / 线：容量压力分",
          leftFormat: fmtPct,
          rightPad: 76,
          bars: [
            { label: "设计利用率", color: colors.amber, value: (row) => row.designUtilizationPct, format: fmtPct },
            { label: "极限利用率", color: colors.red, value: (row) => row.maxUtilizationPct, format: fmtPct },
          ],
          line: {
            label: "容量压力分",
            color: colors.blue,
            value: (row) => row.capacityScore,
            format: fmtQualityScoreDelta,
          },
          valueText: (row) => `设计 ${fmtPct(row.designUtilizationPct)} / 极限 ${fmtPct(row.maxUtilizationPct)}`,
          growthHeader: "容量压力分",
          growthText: (row) => fmtQualityScoreDelta(row.capacityScore),
          metricValue: (aggregate) => aggregate.capacityScore,
        },
        commercialImpact: {
          label: "商业影响乘数",
          caption: "柱：餐饮/免税/奢侈品质量乘数 / 线：感知质量指数",
          leftFormat: fmtMultiplier,
          rightPad: 76,
          bars: [
            { label: "餐饮零售", color: colors.green, value: (row) => row.foodRetailQualityMultiplier, format: fmtMultiplier },
            { label: "免税", color: colors.blue, value: (row) => row.dutyFreeQualityMultiplier, format: fmtMultiplier },
            { label: "奢侈品", color: colors.violet, value: (row) => row.luxuryQualityMultiplier, format: fmtMultiplier },
          ],
          line: {
            label: "感知质量指数",
            color: colors.amber,
            value: (row) => row.qualityIndex,
            format: fmtQualityScore,
          },
          valueText: (row) => [
            `餐饮 ${fmtMultiplier(row.foodRetailQualityMultiplier)}`,
            `免税 ${fmtMultiplier(row.dutyFreeQualityMultiplier)}`,
            `奢侈品 ${fmtMultiplier(row.luxuryQualityMultiplier)}`,
          ].join(" / "),
          growthHeader: "感知质量指数",
          growthText: (row) => fmtQualityScore(row.qualityIndex),
          metricValue: (aggregate) => (
            aggregate.foodRetailQualityMultiplier
            + aggregate.dutyFreeQualityMultiplier
            + aggregate.luxuryQualityMultiplier
          ) / 3,
        },
      };
      return configs[metric] || configs.qualityIndex;
    }

    function serviceQualityPeriodsAll(scope = state.serviceQualityReportScope, metric = state.serviceQualityMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = serviceQualityMetricConfig(metric);
      if (metricConfig.ledgerOnly) return [];
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateServiceQualityPeriod(periodQuarters);
        const previousAggregate = aggregateServiceQualityPeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyDiff = previousQuarters.length ? metricValue - previousMetricValue : 0;
        const yoyPct = previousQuarters.length && previousMetricValue !== 0
          ? ((metricValue - previousMetricValue) / Math.abs(previousMetricValue)) * 100
          : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyDiff,
          yoyPct,
        });
      }
      return rows;
    }

    function serviceQualityVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - SERVICE_QUALITY_WINDOW_SIZE);
      if (state.serviceQualityWindowPinnedToLatest || state.serviceQualityWindowStart == null) {
        state.serviceQualityWindowStart = maxStart;
      }
      state.serviceQualityWindowStart = Math.max(0, Math.min(maxStart, Number(state.serviceQualityWindowStart) || 0));
      return rows.slice(state.serviceQualityWindowStart, state.serviceQualityWindowStart + SERVICE_QUALITY_WINDOW_SIZE);
    }

    function renderServiceQualityAnalysis() {
      const config = serviceQualityMetricConfig();
      if (config.ledgerOnly) {
        renderServiceQualityMaintenanceStatus(config);
        return;
      }
      const allRows = serviceQualityPeriodsAll();
      const rows = serviceQualityVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - SERVICE_QUALITY_WINDOW_SIZE);
      el.serviceQualityMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-service-quality-metric") === state.serviceQualityMetric));
      });
      el.serviceQualityMetricTitle.textContent = config.label;
      el.serviceQualityValueHeader.textContent = config.label;
      el.serviceQualityGrowthHeader.textContent = config.growthHeader;
      el.serviceQualityChartPanel.hidden = false;
      el.serviceQualityMetricTable.hidden = false;
      el.serviceQualityMaintenanceTable.hidden = true;
      el.serviceQualityRangeInput.hidden = false;
      el.serviceQualityTicks.hidden = false;
      el.serviceQualityScopeSelect.value = state.serviceQualityReportScope;
      el.serviceQualityRangeInput.min = "0";
      el.serviceQualityRangeInput.max = String(maxStart);
      el.serviceQualityRangeInput.value = String(state.serviceQualityWindowStart || 0);
      el.serviceQualityRangeInput.disabled = maxStart === 0;
      el.serviceQualityTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, SERVICE_QUALITY_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.serviceQualityTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.serviceQualityMetricCaption.textContent = config.caption;
        el.serviceQualityMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.serviceQualityMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.serviceQualityWindowLabel.textContent = "年度轴";
        el.serviceQualityWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.serviceQualityReportScope);
      el.serviceQualityMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.serviceQualityWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.serviceQualityWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.serviceQualityMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.serviceQualityMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

    function aggregateFacilitiesProjectPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const last = (getter) => {
        if (!quarters.length) return 0;
        return Number(getter(quarters[quarters.length - 1])) || 0;
      };
      const served = sum((quarter) => quarter.demand.quarterServed);
      const designCapacity = sum((quarter) => quarter.capacity.quarterDesignCapacity);
      const maxCapacity = sum((quarter) => quarter.capacity.quarterMaxCapacity);
      const capexOutlay = sum((quarter) => quarter.finance.capexOutlay);
      const demolitionExpense = sum((quarter) => quarter.finance.rebuildDemolitionExpense);
      const oldAssetWriteoff = sum((quarter) => quarter.finance.rebuildOldAssetWriteoff);
      const depreciation = sum((quarter) => quarter.finance.accountingDepreciation);
      const constructionInProgress = last((quarter) => quarter.finance.constructionInProgress);
      const fixedAssetOriginal = last((quarter) => quarter.finance.fixedAssetOriginal);
      const fixedAssetAccumulatedDepreciation = last((quarter) => quarter.finance.fixedAssetAccumulatedDepreciation);
      const fixedAssetBookValue = last((quarter) => quarter.finance.fixedAssetBookValue);
      const totalNoncurrentAssets = last((quarter) => quarter.finance.totalNoncurrentAssets);
      return {
        served,
        designCapacity,
        maxCapacity,
        capexOutlay,
        demolitionExpense,
        oldAssetWriteoff,
        depreciation,
        constructionInProgress,
        fixedAssetOriginal,
        fixedAssetAccumulatedDepreciation,
        fixedAssetBookValue,
        totalNoncurrentAssets,
        designUtilizationPct: designCapacity ? served / designCapacity * 100 : 0,
        maxUtilizationPct: maxCapacity ? served / maxCapacity * 100 : 0,
      };
    }

    function facilitiesProjectMetricConfig(metric = state.facilitiesProjectMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
      };
      const capacityMetric = (key, label, barLabel, color) => ({
        label,
        caption: `柱：${barLabel} / 线：同比增幅`,
        leftFormat: (value) => fmt(value, 0),
        bars: [
          { label: barLabel, color, value: (row) => row[key], format: fmtPassenger },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtPassenger(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
        growthMode: "percentChange",
      });
      const configs = {
        designCapacityChange: capacityMetric("designCapacity", "设计容量变化", "设计容量", colors.blue),
        maxCapacityChange: capacityMetric("maxCapacity", "极限容量变化", "极限容量", colors.muted),
        capexOutlay: {
          label: "工程资本化支出",
          caption: "柱：工程资本化支出 / 线：同比变化",
          leftFormat: fmtMoney,
          rightPad: 76,
          bars: [
            { label: "工程资本化支出", color: colors.red, value: (row) => row.capexOutlay, format: fmtMoney },
          ],
          line: {
            label: "同比变化",
            color: colors.amber,
            value: (row) => row.yoyPct,
            format: fmtMoney,
          },
          valueText: (row) => fmtMoney(row.capexOutlay),
          growthHeader: "同比变化",
          growthText: (row) => fmtMoney(row.yoyPct),
          metricValue: (aggregate) => aggregate.capexOutlay,
          growthMode: "absoluteChange",
        },
        assetStatus: {
          label: "工程资产/固定资产",
          caption: "表：资本化支出、非资本化重建影响与固定资产状态",
          tableOnly: true,
          metricValue: (aggregate) => aggregate.fixedAssetBookValue + aggregate.constructionInProgress,
          growthMode: "absoluteChange",
        },
        assetLedger: {
          label: "资产/项目台账",
          caption: "表：资产台账与项目台账分开展示",
          ledgerOnly: true,
        },
      };
      return configs[metric] || configs.designCapacityChange;
    }

    function facilitiesProjectGrowth(currentValue, previousValue, config) {
      if (config.growthMode === "absoluteChange") return currentValue - previousValue;
      return previousValue !== 0 ? ((currentValue - previousValue) / Math.abs(previousValue)) * 100 : 0;
    }

    function setFacilitiesProjectScopeOptions(config) {
      if (config.ledgerOnly) {
        el.facilitiesProjectScopeControl.hidden = true;
        el.facilitiesProjectLedgerYearControl.hidden = false;
        el.facilitiesProjectLedgerQuarterControl.hidden = false;
        setFacilitiesProjectLedgerPeriodOptions();
        return;
      }
      el.facilitiesProjectScopeControl.hidden = false;
      el.facilitiesProjectLedgerYearControl.hidden = true;
      el.facilitiesProjectLedgerQuarterControl.hidden = true;
      const options = FACILITIES_PROJECT_DEFAULT_SCOPE_OPTIONS;
      if (!options.some((option) => option.value === state.facilitiesProjectReportScope)) {
        state.facilitiesProjectReportScope = options[0]?.value || "latest";
      }
      el.facilitiesProjectScopeSelect.innerHTML = options.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.facilitiesProjectScopeSelect.value = state.facilitiesProjectReportScope;
    }

    function facilitiesProjectLedgerCurrentIndex() {
      if (!state.operations || !state.operations.quarters.length) return -1;
      const minIndex = state.operations.playerStartIndex ?? 0;
      return Math.min(
        Math.max(minIndex, state.operationsQuarterIndex ?? minIndex),
        state.operations.quarters.length - 1,
      );
    }

    function facilitiesProjectLedgerAvailableQuarters() {
      const index = facilitiesProjectLedgerCurrentIndex();
      if (index < 0) return [];
      return state.operations.quarters.slice(0, index + 1);
    }

    function facilitiesProjectLedgerYears() {
      return Array.from(new Set(facilitiesProjectLedgerAvailableQuarters().map((quarter) => Number(quarter.year))))
        .filter((year) => Number.isFinite(year))
        .sort((a, b) => a - b);
    }

    function selectedFacilitiesProjectLedgerYear() {
      const currentQuarter = state.operations?.quarters?.[facilitiesProjectLedgerCurrentIndex()];
      if (!currentQuarter) return null;
      const years = facilitiesProjectLedgerYears();
      const requested = state.facilitiesProjectLedgerYear === "latest"
        ? Number(currentQuarter.year)
        : Number(state.facilitiesProjectLedgerYear);
      if (years.includes(requested)) return requested;
      state.facilitiesProjectLedgerYear = "latest";
      return Number(currentQuarter.year);
    }

    function facilitiesProjectLedgerQuarterOptions(year) {
      const yearQuarters = facilitiesProjectLedgerAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year));
      const seen = new Set();
      const quarterOptions = yearQuarters
        .map((quarter) => quarterNumber(quarter))
        .filter((quarterNo) => {
          if (!quarterNo || seen.has(quarterNo)) return false;
          seen.add(quarterNo);
          return true;
        })
        .sort((a, b) => a - b)
        .map((quarterNo) => ({ value: `q${quarterNo}`, label: `Q${quarterNo}` }));
      return [
        { value: "latest", label: "最新季度" },
        { value: "overview", label: "本年总览" },
        ...quarterOptions,
      ];
    }

    function setFacilitiesProjectLedgerPeriodOptions() {
      const years = facilitiesProjectLedgerYears();
      if (!years.length) {
        el.facilitiesProjectLedgerYearSelect.innerHTML = `<option value="latest">最新</option>`;
        el.facilitiesProjectLedgerQuarterSelect.innerHTML = `<option value="latest">最新季度</option>`;
        state.facilitiesProjectLedgerYear = "latest";
        state.facilitiesProjectLedgerQuarter = "latest";
        return;
      }
      const yearValueAllowed = state.facilitiesProjectLedgerYear === "latest"
        || years.includes(Number(state.facilitiesProjectLedgerYear));
      if (!yearValueAllowed) state.facilitiesProjectLedgerYear = "latest";
      el.facilitiesProjectLedgerYearSelect.innerHTML = [
        `<option value="latest">最新</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.facilitiesProjectLedgerYearSelect.value = state.facilitiesProjectLedgerYear;

      const selectedYear = selectedFacilitiesProjectLedgerYear();
      const quarterOptions = facilitiesProjectLedgerQuarterOptions(selectedYear);
      if (!quarterOptions.some((option) => option.value === state.facilitiesProjectLedgerQuarter)) {
        state.facilitiesProjectLedgerQuarter = "latest";
      }
      el.facilitiesProjectLedgerQuarterSelect.innerHTML = quarterOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.facilitiesProjectLedgerQuarterSelect.value = state.facilitiesProjectLedgerQuarter;
    }

    function splitProjectIds(value) {
      return String(value || "").split(/[;,|\s]+/).map((item) => item.trim()).filter(Boolean);
    }

    function projectIdsContain(value, id) {
      return splitProjectIds(value).includes(id);
    }

    function previousOperationQuarter(quarter) {
      const index = Number(quarter?.index);
      if (!state.operations || !Number.isFinite(index) || index <= 0) return null;
      return state.operations.quarters[index - 1] || null;
    }

    function projectStartedInQuarter(quarter, project) {
      if (!quarter) return false;
      const projects = quarter.projects || {};
      if (project.startedIdsKey && projectIdsContain(projects[project.startedIdsKey], project.id)) return true;
      const previous = previousOperationQuarter(quarter);
      const previousProjects = previous?.projects || {};
      return (
        projectIdsContain(projects[project.activeIdsKey], project.id)
        && !projectIdsContain(previousProjects[project.activeIdsKey], project.id)
        && !projectIdsContain(previousProjects[project.completedIdsKey], project.id)
      );
    }

    function projectCompletedInQuarter(quarter, project) {
      if (!quarter) return false;
      const projects = quarter.projects || {};
      const previousProjects = previousOperationQuarter(quarter)?.projects || {};
      return (
        projectIdsContain(projects[project.completedIdsKey], project.id)
        && !projectIdsContain(previousProjects[project.completedIdsKey], project.id)
      );
    }

    function projectHistoryThrough(quarter) {
      if (!state.operations || !quarter) return [];
      const index = Number(quarter.index);
      if (!Number.isFinite(index)) return [];
      return state.operations.quarters.slice(0, index + 1);
    }

    function projectEverCompleted(project, quarter) {
      return projectHistoryThrough(quarter).some((item) => {
        const projects = item.projects || {};
        return projectIdsContain(projects[project.completedIdsKey], project.id);
      });
    }

    function renovationAssetWrittenOffThrough(quarter) {
      return projectHistoryThrough(quarter).some((item) => Number(item.projects?.rebuildOldRenovationAssetWriteoff) > 0);
    }

    function facilitiesProjectLedgerPeriodSelection() {
      const year = selectedFacilitiesProjectLedgerYear();
      if (!year) return { quarters: [], label: "当前季度", isOverview: false };
      const yearQuarters = facilitiesProjectLedgerAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year))
        .sort((a, b) => Number(a.index) - Number(b.index));
      if (!yearQuarters.length) return { quarters: [], label: `${year}`, isOverview: false };
      if (state.facilitiesProjectLedgerQuarter === "overview") {
        return {
          quarters: yearQuarters,
          label: `${year} 本年总览`,
          isOverview: true,
        };
      }
      const requestedQuarterNo = String(state.facilitiesProjectLedgerQuarter || "").match(/^q([1-4])$/i);
      const selectedQuarter = requestedQuarterNo
        ? yearQuarters.find((quarter) => quarterNumber(quarter) === Number(requestedQuarterNo[1])) || yearQuarters[yearQuarters.length - 1]
        : yearQuarters[yearQuarters.length - 1];
      return {
        quarters: selectedQuarter ? [selectedQuarter] : [],
        label: selectedQuarter?.label || `${year}`,
        isOverview: false,
      };
    }

    function fmtSignedPassenger(value) {
      const number = Number(value) || 0;
      if (!number) return "-";
      return `${number > 0 ? "+" : ""}${fmt(number, 1)} 百万人`;
    }

    function slotRoleLabel(value) {
      return {
        main_slot: "主槽位",
        secondary_slot: "次槽位",
        auxiliary_slot: "辅助槽位",
      }[value] || value || "-";
    }

    function auxiliarySlotDisplayIndex(slotId) {
      const match = String(slotId || "").match(/_SLOT_(\d+)$/);
      if (!match) return "";
      return Math.max(1, Number(match[1]) - 2);
    }

    function slotDisplayLabel(slotRole, slotId) {
      if (slotRole === "main_slot") return "主槽位";
      if (slotRole === "secondary_slot") return "次槽位";
      if (slotRole === "auxiliary_slot") return `辅助槽位${auxiliarySlotDisplayIndex(slotId) || ""}`;
      return slotRoleLabel(slotRole);
    }

    function facilitySizeLabel(value) {
      return {
        empty: "未投运",
        small: "小型",
        medium: "中型",
        large: "大型",
        extra_large: "超大型",
        giant: "巨型",
      }[value] || value || "-";
    }

    function playerActionForLedgerProject(project) {
      return state.playerActions.find((action) => (
        action?.type === "start_project" && action?.projectId === project?.id
      )) || null;
    }

    function standardRenovationLedgerFields(quarters, project, action) {
      const config = action?.eventConfig || {};
      const startIndex = Number(action?.startedAtIndex);
      const duration = Math.max(1, Number(config.duration_quarters) || 0);
      const capexTotal = Math.max(0, Number(config.capex_million_cny) || 0);
      const capacityMultiplier = Math.max(0, Math.min(1, Number(config.construction_capacity_multiplier) || 0.75));
      const usefulLifeYears = Math.max(1, Number(config.useful_life_years) || 20);
      const residualValuePct = Math.max(0, Number(config.residual_value_pct) || 0);
      const completionIndex = startIndex + duration;
      const capexPerQuarter = capexTotal / duration;
      const currentIndex = Number(quarters[quarters.length - 1]?.index);
      const activeQuarter = (quarter) => {
        const index = Number(quarter?.index);
        return Number.isFinite(index) && index >= startIndex && index < completionIndex;
      };
      const capex = quarters.reduce((total, quarter) => total + (activeQuarter(quarter) ? capexPerQuarter : 0), 0);
      const currentActive = Number.isFinite(currentIndex) && currentIndex >= startIndex && currentIndex < completionIndex;
      const completed = Number.isFinite(currentIndex) && currentIndex >= completionIndex;
      const elapsedDepreciationQuarters = completed ? Math.max(0, currentIndex - completionIndex + 1) : 0;
      const residual = capexTotal * residualValuePct / 100;
      const depreciationPerQuarter = (capexTotal - residual) / (usefulLifeYears * 4);
      const accumulatedDepreciation = Math.min(capexTotal - residual, elapsedDepreciationQuarters * depreciationPerQuarter);
      const designCapacity = Number(FACILITY_SIZE_DESIGN_CAPACITY[project.facilitySize]) || 0;
      const maxCapacity = Number(FACILITY_SIZE_MAX_CAPACITY[project.facilitySize]) || 0;
      return {
        capex,
        demolition: 0,
        writeoff: 0,
        cip: currentActive ? capexTotal * Math.max(0, Math.min(1, (currentIndex - startIndex + 1) / duration)) : 0,
        original: completed ? capexTotal : 0,
        accumulatedDepreciation,
        book: completed ? Math.max(capexTotal - accumulatedDepreciation, residual) : 0,
        depreciation: quarters.reduce((total, quarter) => (
          Number(quarter?.index) >= completionIndex ? total + depreciationPerQuarter : total
        ), 0),
        designLoss: quarters.some(activeQuarter) ? designCapacity * (1 - capacityMultiplier) : 0,
        maxLoss: quarters.some(activeQuarter) ? maxCapacity * (1 - capacityMultiplier) : 0,
        designDelta: 0,
        maxDelta: 0,
      };
    }

    function standardRebuildLedgerFields(quarters, project, action) {
      const config = action?.eventConfig || {};
      const startIndex = Number(action?.startedAtIndex);
      const duration = Math.max(1, Number(config.duration_quarters) || 1);
      const capexTotal = Math.max(0, Number(config.asset_capex_million_cny) || 0);
      const demolitionTotal = Math.max(0, Number(config.demolition_expense_million_cny) || 0);
      const usefulLifeYears = Math.max(1, Number(config.useful_life_years) || 40);
      const residualValuePct = Math.max(0, Number(config.residual_value_pct) || 0);
      const completionIndex = startIndex + duration;
      const currentIndex = Number(quarters[quarters.length - 1]?.index);
      const activeQuarter = (quarter) => Number(quarter?.index) >= startIndex && Number(quarter?.index) < completionIndex;
      const active = Number.isFinite(currentIndex) && currentIndex >= startIndex && currentIndex < completionIndex;
      const completed = Number.isFinite(currentIndex) && currentIndex >= completionIndex;
      const capex = quarters.reduce((total, quarter) => total + (activeQuarter(quarter) ? capexTotal / duration : 0), 0);
      const demolition = quarters.reduce((total, quarter) => total + (activeQuarter(quarter) ? demolitionTotal / duration : 0), 0);
      const elapsedDepreciationQuarters = completed ? Math.max(0, currentIndex - completionIndex + 1) : 0;
      const residual = capexTotal * residualValuePct / 100;
      const depreciationPerQuarter = (capexTotal - residual) / (usefulLifeYears * 4);
      const accumulatedDepreciation = Math.min(capexTotal - residual, elapsedDepreciationQuarters * depreciationPerQuarter);
      const sourceSize = config.source_facility_size || project.sourceFacilitySize;
      const targetSize = config.target_facility_size || project.facilitySize;
      return {
        capex,
        demolition,
        writeoff: 0,
        cip: active ? capexTotal * Math.max(0, Math.min(1, (currentIndex - startIndex + 1) / duration)) : 0,
        original: completed ? capexTotal : 0,
        accumulatedDepreciation,
        book: completed ? Math.max(capexTotal - accumulatedDepreciation, residual) : 0,
        depreciation: quarters.reduce((total, quarter) => Number(quarter?.index) >= completionIndex ? total + depreciationPerQuarter : total, 0),
        designLoss: quarters.some(activeQuarter) ? Number(FACILITY_SIZE_DESIGN_CAPACITY[sourceSize]) || 0 : 0,
        maxLoss: quarters.some(activeQuarter) ? Number(FACILITY_SIZE_MAX_CAPACITY[sourceSize]) || 0 : 0,
        designDelta: completed
          ? (Number(FACILITY_SIZE_DESIGN_CAPACITY[targetSize]) || 0) - (Number(FACILITY_SIZE_DESIGN_CAPACITY[sourceSize]) || 0)
          : 0,
        maxDelta: completed
          ? (Number(FACILITY_SIZE_MAX_CAPACITY[targetSize]) || 0) - (Number(FACILITY_SIZE_MAX_CAPACITY[sourceSize]) || 0)
          : 0,
      };
    }

    function standardConstructionLedgerFields(quarters, project, action) {
      const config = action?.eventConfig || {};
      const startIndex = Number(action?.startedAtIndex);
      const duration = Math.max(1, Number(config.duration_quarters) || 1);
      const capexTotal = Math.max(0, Number(config.capex_million_cny) || 0);
      const usefulLifeYears = Math.max(1, Number(config.useful_life_years) || 40);
      const residualValuePct = Math.max(0, Number(config.residual_value_pct) || 0);
      const completionIndex = startIndex + duration;
      const currentIndex = Number(quarters[quarters.length - 1]?.index);
      const activeQuarter = (quarter) => Number(quarter?.index) >= startIndex && Number(quarter?.index) < completionIndex;
      const active = Number.isFinite(currentIndex) && currentIndex >= startIndex && currentIndex < completionIndex;
      const completed = Number.isFinite(currentIndex) && currentIndex >= completionIndex;
      const capex = quarters.reduce((total, quarter) => total + (activeQuarter(quarter) ? capexTotal / duration : 0), 0);
      const elapsedDepreciationQuarters = completed ? Math.max(0, currentIndex - completionIndex + 1) : 0;
      const residual = capexTotal * residualValuePct / 100;
      const depreciationPerQuarter = (capexTotal - residual) / (usefulLifeYears * 4);
      const accumulatedDepreciation = Math.min(capexTotal - residual, elapsedDepreciationQuarters * depreciationPerQuarter);
      return {
        capex,
        demolition: 0,
        writeoff: 0,
        cip: active ? capexTotal * Math.max(0, Math.min(1, (currentIndex - startIndex + 1) / duration)) : 0,
        original: completed ? capexTotal : 0,
        accumulatedDepreciation,
        book: completed ? Math.max(capexTotal - accumulatedDepreciation, residual) : 0,
        depreciation: quarters.reduce((total, quarter) => Number(quarter?.index) >= completionIndex ? total + depreciationPerQuarter : total, 0),
        designLoss: 0,
        maxLoss: 0,
        designDelta: completed ? Number(FACILITY_SIZE_DESIGN_CAPACITY[project.facilitySize]) || 0 : 0,
        maxDelta: completed ? Number(FACILITY_SIZE_MAX_CAPACITY[project.facilitySize]) || 0 : 0,
      };
    }

    function aggregateProjectLedgerFields(quarters, project) {
      const playerAction = playerActionForLedgerProject(project);
      if (project.type === "翻新" && playerAction?.eventConfig) {
        return standardRenovationLedgerFields(quarters, project, playerAction);
      }
      if (["拆除重建", "拆除"].includes(project.type) && playerAction?.eventConfig) {
        return standardRebuildLedgerFields(quarters, project, playerAction);
      }
      if (project.type === "新建" && playerAction?.eventConfig) {
        return standardConstructionLedgerFields(quarters, project, playerAction);
      }
      const sumProject = (key) => key ? quarters.reduce((total, quarter) => total + (Number(quarter.projects?.[key]) || 0), 0) : 0;
      const lastProject = (key) => {
        if (!key || !quarters.length) return 0;
        return Number(quarters[quarters.length - 1].projects?.[key]) || 0;
      };
      const maxProject = (key) => key ? quarters.reduce((value, quarter) => Math.max(value, Number(quarter.projects?.[key]) || 0), 0) : 0;
      return {
        capex: sumProject(project.capexKey),
        demolition: sumProject(project.demolitionKey),
        writeoff: sumProject(project.writeoffKey),
        cip: lastProject(project.cipKey),
        original: lastProject(project.originalKey),
        accumulatedDepreciation: lastProject(project.accumulatedDepreciationKey),
        book: lastProject(project.bookKey),
        depreciation: sumProject(project.depreciationKey),
        designLoss: maxProject(project.designLossKey),
        maxLoss: maxProject(project.maxLossKey),
        designDelta: maxProject(project.designDeltaKey),
        maxDelta: maxProject(project.maxDeltaKey),
      };
    }

    function projectLedgerStatus(project, quarters, isOverview = false) {
      const currentScope = !isOverview;
      const currentQuarter = quarters[quarters.length - 1];
      if (!currentQuarter) return "暂无数据";
      const currentProjects = currentQuarter.projects || {};
      const activeNow = projectIdsContain(currentProjects[project.activeIdsKey], project.id);
      const completedNow = projectCompletedInQuarter(currentQuarter, project);
      const completed = projectIdsContain(currentProjects[project.completedIdsKey], project.id);
      if (currentScope) {
        if (project.type === "翻新" && renovationAssetWrittenOffThrough(currentQuarter)) return "已被重建减记";
        if (completedNow) return "本季完工/转固";
        if (projectStartedInQuarter(currentQuarter, project)) return "本季开工";
        if (activeNow) return "施工中";
        if (completed || projectEverCompleted(project, currentQuarter)) return "使用中折旧";
        return "规划未启动";
      }
      if (project.type === "翻新" && quarters.some((quarter) => Number(quarter.projects?.rebuildOldRenovationAssetWriteoff) > 0)) {
        return "年内被重建减记";
      }
      if (project.type === "翻新" && renovationAssetWrittenOffThrough(currentQuarter)) return "已被重建减记";
      if (quarters.some((quarter) => projectCompletedInQuarter(quarter, project))) return "年内完工/转固";
      if (quarters.some((quarter) => projectStartedInQuarter(quarter, project))) return "年内开工";
      if (quarters.some((quarter) => projectIdsContain(quarter.projects?.[project.activeIdsKey], project.id))) return "年内施工";
      if (completed || projectEverCompleted(project, currentQuarter)) return "使用中折旧";
      return "本年无进展";
    }

    function projectLedgerStage(project, quarters, isOverview = false) {
      const currentQuarter = quarters[quarters.length - 1];
      if (!currentQuarter) return "-";
      const currentProjects = currentQuarter.projects || {};
      const activeNow = projectIdsContain(currentProjects[project.activeIdsKey], project.id);
      const completed = projectIdsContain(currentProjects[project.completedIdsKey], project.id);
      if (project.type === "翻新" && renovationAssetWrittenOffThrough(currentQuarter)) return "已退役";
      if (activeNow) return isOverview ? "年内处于施工期" : "施工期";
      if (projectCompletedInQuarter(currentQuarter, project)) return "本季转固";
      if (completed || projectEverCompleted(project, currentQuarter)) return "投运使用";
      return "尚未进入资产形成期";
    }

    function projectLedgerCapacityImpact(project, aggregate) {
      const parts = [];
      if (aggregate.designLoss || aggregate.maxLoss) {
        parts.push(`施工损失：设计 ${fmtSignedPassenger(-aggregate.designLoss)} / 极限 ${fmtSignedPassenger(-aggregate.maxLoss)}`);
      }
      if (aggregate.designDelta || aggregate.maxDelta) {
        parts.push(`转固增量：设计 ${fmtSignedPassenger(aggregate.designDelta)} / 极限 ${fmtSignedPassenger(aggregate.maxDelta)}`);
      }
      if (!parts.length && project.type === "新建" && aggregate.book > 0) return "新增槽位投运";
      return parts.join("；") || "-";
    }

    function projectById(id) {
      return facilityLedgerProjects().find((project) => project.id === id);
    }

    function clampNumber(value, min, max) {
      return Math.min(max, Math.max(min, Number(value) || 0));
    }

    function quarterStartFraction(quarter) {
      return Number(quarter?.year || 0) + ((quarterNumber(quarter) || 1) - 1) / 4;
    }

    function assetProfileAtFraction(asset, fraction) {
      const serviceStart = Number(asset.inServiceYear);
      const original = Number(asset.original) || 0;
      const usefulLife = Number(asset.usefulLifeYears) || 0;
      if (!original || !usefulLife || !Number.isFinite(fraction) || fraction <= serviceStart) return emptyAssetLedgerFields();
      const residual = original * (Number(asset.residualValuePct) || 0) / 100;
      const annualDepreciation = (original - residual) / usefulLife;
      const elapsed = clampNumber(fraction - serviceStart, 0, usefulLife);
      const accumulatedDepreciation = annualDepreciation * elapsed;
      return {
        original,
        accumulatedDepreciation,
        book: Math.max(original - accumulatedDepreciation, residual),
        depreciation: 0,
      };
    }

    function rawAssetProfileForQuarter(asset, quarter) {
      if (!quarter) return emptyAssetLedgerFields();
      const startFraction = quarterStartFraction(quarter);
      const endFraction = startFraction + 0.25;
      const serviceStart = Number(asset.inServiceYear);
      const original = Number(asset.original) || 0;
      const usefulLife = Number(asset.usefulLifeYears) || 0;
      if (!original || !usefulLife || endFraction <= serviceStart) return emptyAssetLedgerFields();
      const residual = original * (Number(asset.residualValuePct) || 0) / 100;
      const annualDepreciation = (original - residual) / usefulLife;
      const elapsedStart = clampNumber(startFraction - serviceStart, 0, usefulLife);
      const elapsedEnd = clampNumber(endFraction - serviceStart, 0, usefulLife);
      const accumulatedStart = annualDepreciation * elapsedStart;
      const accumulatedEnd = annualDepreciation * elapsedEnd;
      return {
        original,
        accumulatedDepreciation: accumulatedEnd,
        book: Math.max(original - accumulatedEnd, residual),
        depreciation: Math.max(0, accumulatedEnd - accumulatedStart),
      };
    }

    function assetProfileForQuarter(asset, quarter) {
      if (!quarter || initialAssetDisposedThrough(asset, quarter)) return emptyAssetLedgerFields();
      return rawAssetProfileForQuarter(asset, quarter);
    }

    function emptyAssetLedgerFields() {
      return {
        original: 0,
        accumulatedDepreciation: 0,
        book: 0,
        depreciation: 0,
      };
    }

    function combineAssetLedgerFields(parts) {
      return parts.reduce((row, part) => ({
        original: row.original + (Number(part.original) || 0),
        accumulatedDepreciation: row.accumulatedDepreciation + (Number(part.accumulatedDepreciation) || 0),
        book: row.book + (Number(part.book) || 0),
        depreciation: row.depreciation + (Number(part.depreciation) || 0),
      }), emptyAssetLedgerFields());
    }

    function initialAssetDisposedThrough(asset, quarter) {
      return projectHistoryThrough(quarter).some((item) => (
        projectIdsContain(item.projects?.rebuildStartedSlotIds, asset.slotId)
      ));
    }

    function initialAssetDisposalQuarter(asset, quarter) {
      return projectHistoryThrough(quarter).find((item) => (
        projectIdsContain(item.projects?.rebuildStartedSlotIds, asset.slotId)
      )) || null;
    }

    function initialAssetRetiredFields(asset, quarter) {
      const disposalQuarter = initialAssetDisposalQuarter(asset, quarter);
      if (!disposalQuarter) return emptyAssetLedgerFields();
      const writeoff = Number(disposalQuarter.projects?.rebuildOldInitialAssetWriteoff) || 0;
      const disposalProfile = assetProfileAtFraction(asset, quarterStartFraction(disposalQuarter));
      return {
        original: Number(asset.original) || 0,
        accumulatedDepreciation: Math.max(0, (Number(asset.original) || 0) - (writeoff || disposalProfile.book)),
        book: 0,
        depreciation: 0,
      };
    }

    function initialAssetLedgerFields(asset, quarters) {
      const currentQuarter = quarters[quarters.length - 1];
      const current = initialAssetDisposedThrough(asset, currentQuarter)
        ? initialAssetRetiredFields(asset, currentQuarter)
        : assetProfileForQuarter(asset, currentQuarter);
      return {
        ...current,
        depreciation: quarters.reduce((total, quarter) => total + assetProfileForQuarter(asset, quarter).depreciation, 0),
      };
    }

    function projectAssetLedgerFields(project, quarters) {
      const aggregate = aggregateProjectLedgerFields(quarters, project);
      return {
        original: aggregate.original,
        accumulatedDepreciation: aggregate.accumulatedDepreciation,
        book: aggregate.book,
        depreciation: aggregate.depreciation,
      };
    }

    function projectActiveInScope(project, quarters) {
      return quarters.some((quarter) => projectIdsContain(quarter.projects?.[project.activeIdsKey], project.id));
    }

    function projectActiveNow(project, quarter) {
      return projectIdsContain(quarter?.projects?.[project.activeIdsKey], project.id);
    }

    function projectCompletedThrough(project, quarter) {
      if (!quarter) return false;
      return (
        projectIdsContain(quarter.projects?.[project.completedIdsKey], project.id)
        || projectEverCompleted(project, quarter)
      );
    }

    function projectHasLedgerActivity(project, quarter) {
      return projectHistoryThrough(quarter).some((item) => {
        const projects = item.projects || {};
        return (
          projectStartedInQuarter(item, project)
          || projectIdsContain(projects[project.startedIdsKey], project.id)
          || projectIdsContain(projects[project.activeIdsKey], project.id)
          || projectIdsContain(projects[project.completedIdsKey], project.id)
        );
      });
    }

    function projectLedgerSimpleStatus(project, quarters) {
      const currentQuarter = quarters[quarters.length - 1];
      if (!currentQuarter) return "未启动";
      if (projectCompletedThrough(project, currentQuarter)) return "已完成";
      if (projectActiveNow(project, currentQuarter) || projectActiveInScope(project, quarters)) return "施工中";
      return "未启动";
    }

    function projectLedgerTiming(project, quarter) {
      const history = projectHistoryThrough(quarter);
      const started = history.find((item) => (
        projectStartedInQuarter(item, project)
        || projectIdsContain(item.projects?.[project.startedIdsKey], project.id)
        || projectIdsContain(item.projects?.[project.activeIdsKey], project.id)
      ));
      const completed = history.find((item) => (
        projectCompletedInQuarter(item, project)
        || projectIdsContain(item.projects?.[project.completedIdsKey], project.id)
      ));
      return `${started?.label || "未启动"} / ${completed?.label || "-"}`;
    }

    function initialAssetRow(asset, quarters, capacityStatus = "正常可用") {
      if (!asset) return null;
      const currentQuarter = quarters[quarters.length - 1];
      const disposed = initialAssetDisposedThrough(asset, currentQuarter);
      const fields = initialAssetLedgerFields(asset, quarters);
      return {
        name: slotDisplayName(asset.slotId, asset.name),
        airport: asset.airport,
        slotId: asset.slotId,
        slotLabel: slotDisplayLabel(asset.slotRole, asset.slotId),
        facilitySize: facilitySizeLabel(asset.facilitySize),
        status: disposed ? "已退役" : "使用中",
        ...fields,
        capacityStatus: disposed ? "拆除重建退役" : capacityStatus,
      };
    }

    function projectAssetRetiredFields(project, quarter) {
      const history = projectHistoryThrough(quarter);
      const lastOriginal = [...history].reverse()
        .map((item) => Number(item.projects?.[project.originalKey]) || 0)
        .find((value) => value > 0) || 0;
      const writeoff = [...history].reverse()
        .map((item) => Number(item.projects?.rebuildOldRenovationAssetWriteoff) || 0)
        .find((value) => value > 0) || 0;
      return {
        original: lastOriginal,
        accumulatedDepreciation: Math.max(0, lastOriginal - writeoff),
        book: 0,
        depreciation: 0,
      };
    }

    function projectFixedAssetRow(project, quarters, overrides = {}) {
      const currentQuarter = quarters[quarters.length - 1];
      if (project?.type === "拆除") return null;
      if (
        !projectHasLedgerActivity(project, currentQuarter)
        || !projectCompletedThrough(project, currentQuarter)
      ) return null;
      const retired = project.type === "翻新" && renovationAssetWrittenOffThrough(currentQuarter);
      return {
        name: overrides.name || projectDisplayName(project),
        airport: project.airport,
        slotId: project.slotId,
        slotLabel: slotDisplayLabel(project.slotRole, project.slotId),
        facilitySize: facilitySizeLabel(project.facilitySize),
        status: retired ? "已退役" : "使用中",
        ...(retired ? projectAssetRetiredFields(project, currentQuarter) : projectAssetLedgerFields(project, quarters)),
        capacityStatus: retired ? "拆除重建退役" : (overrides.capacityStatus || "正常可用"),
      };
    }

    function slotAssetAdditionRows(slotId, fallbackName, quarters) {
      return slotProjects(slotId)
        .filter((project) => ["翻新", "拆除重建"].includes(project.type))
        .sort((left, right) => {
          const leftStart = Number(projectStartQuarter(left, quarters[quarters.length - 1])?.index);
          const rightStart = Number(projectStartQuarter(right, quarters[quarters.length - 1])?.index);
          return (Number.isFinite(leftStart) ? leftStart : Number.MAX_SAFE_INTEGER)
            - (Number.isFinite(rightStart) ? rightStart : Number.MAX_SAFE_INTEGER);
        })
        .map((project, index) => projectFixedAssetRow(project, quarters, {
          name: `${slotDisplayName(slotId, fallbackName)}-${index + 2}`,
          capacityStatus: project.type === "翻新" ? "翻新转固" : "重建后投运",
        }));
    }

    function buildFacilitiesAssetLedgerRows(quarters) {
      if (!quarters.length) return [];
      const initialRows = [
        initialAssetRow(FACILITY_LEDGER_INITIAL_ASSETS.find((asset) => asset.slotId === "PEK_SLOT_1"), quarters),
        ...slotAssetAdditionRows("PEK_SLOT_1", "首都T3航站楼", quarters),
        initialAssetRow(FACILITY_LEDGER_INITIAL_ASSETS.find((asset) => asset.slotId === "PEK_SLOT_2"), quarters),
        ...slotAssetAdditionRows("PEK_SLOT_2", "首都T2航站楼", quarters),
        initialAssetRow(FACILITY_LEDGER_INITIAL_ASSETS.find((asset) => asset.slotId === "PKX_SLOT_1"), quarters),
        ...slotAssetAdditionRows("PKX_SLOT_1", "大兴T1航站楼", quarters),
      ];
      const constructionRows = facilityLedgerProjects()
        .filter((project) => project.type === "新建")
        .sort((left, right) => {
          const leftStart = Number(projectStartQuarter(left, quarters[quarters.length - 1])?.index);
          const rightStart = Number(projectStartQuarter(right, quarters[quarters.length - 1])?.index);
          return leftStart - rightStart;
        })
        .map((project) => projectFixedAssetRow(project, quarters, {
          name: project.terminalName || projectDisplayName(project),
          capacityStatus: "新增投运",
        }));
      return [...initialRows, ...constructionRows].filter(Boolean);
    }

    function buildProjectLedgerRow(project, quarters) {
      const currentQuarter = quarters[quarters.length - 1];
      const history = projectHistoryThrough(currentQuarter);
      const aggregate = aggregateProjectLedgerFields(history, project);
      return {
        name: projectDisplayName(project),
        airport: project.airport,
        slotId: project.slotId,
        slotLabel: slotDisplayLabel(project.slotRole, project.slotId),
        type: project.type,
        status: projectLedgerSimpleStatus(project, quarters),
        timing: projectLedgerTiming(project, currentQuarter),
        capex: aggregate.capex,
        demolition: aggregate.demolition,
        writeoff: aggregate.writeoff,
        cip: aggregate.cip,
        capacityImpact: projectLedgerCapacityImpact(project, aggregate),
      };
    }

    function buildFacilitiesProjectLedgerRows(quarters) {
      if (!quarters.length) return [];
      const currentQuarter = quarters[quarters.length - 1];
      return facilityLedgerProjects()
        .filter((project) => projectHasLedgerActivity(project, currentQuarter))
        .map((project) => buildProjectLedgerRow(project, quarters));
    }

    function renderFacilitiesProjectLedger(config) {
      const selection = facilitiesProjectLedgerPeriodSelection();
      const quarters = selection.quarters;
      const periodLabel = selection.label;
      const assetRows = buildFacilitiesAssetLedgerRows(quarters, selection.isOverview);
      const projectRows = buildFacilitiesProjectLedgerRows(quarters, selection.isOverview);
      el.facilitiesProjectMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-facilities-project-metric") === state.facilitiesProjectMetric));
      });
      el.facilitiesProjectMetricTitle.textContent = config.label;
      el.facilitiesProjectMetricCaption.textContent = `${periodLabel}；${config.caption}`;
      el.facilitiesProjectMetricTable.hidden = true;
      el.facilitiesProjectLedgerTables.hidden = false;
      el.facilitiesProjectMetricChart.hidden = true;
      el.facilitiesProjectMetricChart.innerHTML = "";
      el.facilitiesProjectRangeInput.hidden = true;
      el.facilitiesProjectTicks.hidden = true;
      el.facilitiesProjectRangeInput.disabled = true;
      el.facilitiesProjectRangeInput.min = "0";
      el.facilitiesProjectRangeInput.max = "0";
      el.facilitiesProjectRangeInput.value = "0";
      el.facilitiesProjectWindowLabel.textContent = periodLabel;
      el.facilitiesProjectWindowHint.textContent = "通过年份和季度查询历史";
      el.facilitiesProjectAssetLedgerCaption.textContent = `${periodLabel}；每个槽位的固定资产状态`;
      el.facilitiesProjectProjectLedgerCaption.textContent = `${periodLabel}；只显示实际已启动的项目`;
      if (!state.operations) {
        el.facilitiesProjectAssetLedgerRows.innerHTML = `<tr><td colspan="10" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.facilitiesProjectProjectLedgerRows.innerHTML = `<tr><td colspan="11" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        return;
      }
      el.facilitiesProjectAssetLedgerRows.innerHTML = assetRows.length ? assetRows.map((row) => `
        <tr>
          <td>${escapeHtml(row.name)}</td>
          <td>${escapeHtml(row.airport)}</td>
          <td>${escapeHtml(row.slotLabel)}</td>
          <td>${escapeHtml(row.facilitySize)}</td>
          <td>${escapeHtml(row.status)}</td>
          <td>${fmtMoney(row.original)}</td>
          <td>${fmtMoney(row.accumulatedDepreciation)}</td>
          <td>${fmtMoney(row.book)}</td>
          <td>${fmtMoney(row.depreciation)}</td>
          <td>${escapeHtml(row.capacityStatus)}</td>
        </tr>
      `).join("") : `<tr><td colspan="10" style="text-align:center;color:var(--muted)">暂无已形成资产</td></tr>`;
      el.facilitiesProjectProjectLedgerRows.innerHTML = projectRows.length ? projectRows.map((row) => `
        <tr>
          <td>${escapeHtml(row.name)}</td>
          <td>${escapeHtml(row.airport)}</td>
          <td>${escapeHtml(row.slotLabel)}</td>
          <td>${escapeHtml(row.type)}</td>
          <td>${escapeHtml(row.status)}</td>
          <td>${escapeHtml(row.timing)}</td>
          <td>${fmtMoney(row.capex)}</td>
          <td>${fmtMoney(row.demolition)}</td>
          <td>${fmtMoney(row.writeoff)}</td>
          <td>${fmtMoney(row.cip)}</td>
          <td>${escapeHtml(row.capacityImpact)}</td>
        </tr>
      `).join("") : `<tr><td colspan="11" style="text-align:center;color:var(--muted)">暂无已启动项目</td></tr>`;
    }

    function facilitiesProjectPeriodsAll(scope = state.facilitiesProjectReportScope, metric = state.facilitiesProjectMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = facilitiesProjectMetricConfig(metric);
      if (metricConfig.ledgerOnly) return [];
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateFacilitiesProjectPeriod(periodQuarters);
        const previousAggregate = aggregateFacilitiesProjectPeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyPct = previousQuarters.length
          ? facilitiesProjectGrowth(metricValue, previousMetricValue, metricConfig)
          : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function facilitiesProjectVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - FACILITIES_PROJECT_WINDOW_SIZE);
      if (state.facilitiesProjectWindowPinnedToLatest || state.facilitiesProjectWindowStart == null) {
        state.facilitiesProjectWindowStart = maxStart;
      }
      state.facilitiesProjectWindowStart = Math.max(0, Math.min(maxStart, Number(state.facilitiesProjectWindowStart) || 0));
      return rows.slice(state.facilitiesProjectWindowStart, state.facilitiesProjectWindowStart + FACILITIES_PROJECT_WINDOW_SIZE);
    }

    function renderFacilitiesProjectAnalysis() {
      const config = facilitiesProjectMetricConfig();
      setFacilitiesProjectScopeOptions(config);
      if (config.ledgerOnly) {
        renderFacilitiesProjectLedger(config);
        return;
      }
      el.facilitiesProjectMetricTable.hidden = false;
      el.facilitiesProjectLedgerTables.hidden = true;
      const allRows = facilitiesProjectPeriodsAll();
      const rows = facilitiesProjectVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - FACILITIES_PROJECT_WINDOW_SIZE);
      el.facilitiesProjectMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-facilities-project-metric") === state.facilitiesProjectMetric));
      });
      el.facilitiesProjectMetricTitle.textContent = config.label;
      el.facilitiesProjectMetricChart.hidden = Boolean(config.tableOnly);
      el.facilitiesProjectRangeInput.hidden = false;
      el.facilitiesProjectTicks.hidden = false;
      el.facilitiesProjectHeaderRow.innerHTML = config.tableOnly
        ? `
          <th>期间</th>
          <th>工程资本化支出</th>
          <th>拆除费用</th>
          <th>旧资产减记</th>
          <th>未转固工程余额</th>
          <th>固定资产原值</th>
          <th>累计折旧</th>
          <th>固定资产账面</th>
          <th>本期折旧</th>
        `
        : `
          <th>期间</th>
          <th>${escapeHtml(config.label)}</th>
          <th>${escapeHtml(config.growthHeader)}</th>
        `;
      el.facilitiesProjectScopeSelect.value = state.facilitiesProjectReportScope;
      el.facilitiesProjectRangeInput.min = "0";
      el.facilitiesProjectRangeInput.max = String(maxStart);
      el.facilitiesProjectRangeInput.value = String(state.facilitiesProjectWindowStart || 0);
      el.facilitiesProjectRangeInput.disabled = maxStart === 0;
      el.facilitiesProjectTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, FACILITIES_PROJECT_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.facilitiesProjectTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.facilitiesProjectMetricCaption.textContent = config.caption;
        el.facilitiesProjectMetricChart.innerHTML = config.tableOnly ? "" : `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.facilitiesProjectMetricRows.innerHTML = `<tr><td colspan="${config.tableOnly ? 9 : 3}" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.facilitiesProjectWindowLabel.textContent = "年度轴";
        el.facilitiesProjectWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.facilitiesProjectReportScope);
      el.facilitiesProjectMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.facilitiesProjectWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.facilitiesProjectWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      if (config.tableOnly) {
        el.facilitiesProjectMetricChart.innerHTML = "";
        el.facilitiesProjectMetricRows.innerHTML = rows.slice().reverse().map((row) => `
          <tr>
            <td>${escapeHtml(row.label)}</td>
            <td>${fmtMoney(row.capexOutlay)}</td>
            <td>${fmtMoney(row.demolitionExpense)}</td>
            <td>${fmtMoney(row.oldAssetWriteoff)}</td>
            <td>${fmtMoney(row.constructionInProgress)}</td>
            <td>${fmtMoney(row.fixedAssetOriginal)}</td>
            <td>${fmtMoney(row.fixedAssetAccumulatedDepreciation)}</td>
            <td>${fmtMoney(row.fixedAssetBookValue)}</td>
            <td>${fmtMoney(row.depreciation)}</td>
          </tr>
        `).join("");
        return;
      }
      renderComboChart(el.facilitiesProjectMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        line: config.line,
      });
      el.facilitiesProjectMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

