const text = (id, value) => {
      document.getElementById(id).textContent = value ?? "—";
    };

    async function loadWorkspaceStatus() {
      const state = document.getElementById("serviceState");
      try {
        const response = await fetch("/api/workspace-status", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const status = await response.json();
        const release = status.viewerRelease || {};
        state.classList.add("ready");
        text("serviceStateText", "本地服务正常");
        text(
          "releaseMode",
          release.mode === "versioned_release" ? "版本化发布" : "兼容数据模式"
        );
        text("releaseRun", release.runId || (release.mode === "legacy_canonical" ? "当前 canonical 输出" : "—"));
        text("releaseVariant", release.variant || "—");
        text("releaseSeed", release.seed ?? "—");
        text("releaseModel", release.modelVersion || `服务 ${status.modelVersion}`);
        text("releaseTime", release.generatedAt || "—");
        text("cachedRunCount", status.cachedRunCount ?? 0);
        text("saveCount", status.saveCount ?? 0);
      } catch (error) {
        state.classList.add("error");
        text("serviceStateText", "无法读取本地服务状态");
        text("releaseMode", "状态不可用");
      }
    }

    loadWorkspaceStatus();
