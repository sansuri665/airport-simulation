window.AirportForecastDataClient = (() => {
  const loadScript = (source) => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = source;
    script.onload = () => resolve(source);
    script.onerror = () => reject(new Error(`无法加载 ${source}`));
    document.head.appendChild(script);
  });

  async function loadAuditIndex(playerIndex) {
    if (window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX) {
      return window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX;
    }
    if (!playerIndex?.auditIndexUrl) {
      throw new Error("当前数据发布未提供独立开发审计入口");
    }
    await loadScript(playerIndex.auditIndexUrl);
    if (!window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX) {
      throw new Error("开发审计索引没有正确注册");
    }
    return window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX;
  }

  async function loadReport(index, reportId) {
    const report = (index?.reports || []).find((item) => item.reportId === reportId);
    if (!report) throw new Error(`预测目录中不存在报告 ${reportId}`);
    const response = await fetch(new URL(report.file, index.baseUrl), { cache: "force-cache" });
    if (!response.ok) throw new Error(`报告 ${reportId} 加载失败：HTTP ${response.status}`);
    const chunk = await response.json();
    if (
      chunk.schemaVersion !== index.chunkSchemaVersion
      || chunk.dataMode !== index.dataMode
      || chunk.reportId !== reportId
    ) {
      throw new Error(`报告 ${reportId} 的数据协议不匹配`);
    }
    if (!Array.isArray(chunk.rows) || chunk.rows.length !== report.rowCount) {
      throw new Error(`报告 ${reportId} 的数据行数不匹配`);
    }
    return chunk.rows;
  }

  async function readApiResponse(response) {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.ok !== true) {
      throw new Error(payload.message || payload.error || `本地服务请求失败：HTTP ${response.status}`);
    }
    return payload;
  }

  async function loadCandidateCatalog() {
    const response = await fetch("/api/forecast-candidate-catalog", { cache: "no-store" });
    return readApiResponse(response);
  }

  async function generateCandidate(request) {
    const response = await fetch("/api/forecast-candidate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return readApiResponse(response);
  }

  return { loadAuditIndex, loadReport, loadCandidateCatalog, generateCandidate };
})();
