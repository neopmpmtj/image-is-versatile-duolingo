(function () {
    const select = document.getElementById("id_vision_model");
    const panel = document.getElementById("model-status-panel");
    const analyzeBtn = document.getElementById("analyze-btn");
    const form = document.getElementById("new-analysis-form");
    const langInput = document.getElementById("id_ui_lang");
    if (!select || !panel || !analyzeBtn) {
        return;
    }

    const FETCH_MS = 20000;
    let inflight = null;

    function syncLangField() {
        if (langInput) {
            langInput.value = currentLang();
        }
    }

    if (form) {
        form.addEventListener("submit", syncLangField);
    }
    syncLangField();
    document.addEventListener("iiv-lang-changed", syncLangField);

    const statusUrlTemplate = document.body.getAttribute("data-model-status-url");
    if (!statusUrlTemplate) {
        return;
    }

    function setStatus(ok, message) {
        panel.textContent = message;
        panel.classList.remove("ok", "error");
        panel.classList.add(ok ? "ok" : "error");
        analyzeBtn.disabled = !ok;
        panel.setAttribute("title", t("clickToRecheckModel"));
    }

    async function checkModel(modelId, forceRecheck) {
        if (!modelId) {
            setStatus(false, t("select_model_to_check"));
            return;
        }
        if (inflight) {
            inflight.abort();
        }
        const controller = new AbortController();
        inflight = controller;
        const timer = setTimeout(function () {
            controller.abort();
        }, FETCH_MS);
        panel.textContent = t("checking_model_availability");
        panel.classList.remove("ok", "error");
        analyzeBtn.disabled = true;
        try {
            let url = statusUrlTemplate.replace("__id__", encodeURIComponent(modelId));
            if (forceRecheck) {
                url += (url.indexOf("?") === -1 ? "?" : "&") + "recheck=1";
            }
            const response = await fetch(url, { signal: controller.signal });
            const data = await response.json();
            if (inflight !== controller) {
                return;
            }
            setStatus(data.ok, apiErrorMessage(data));
        } catch (err) {
            if (inflight !== controller) {
                return;
            }
            setStatus(false, t("could_not_check_model"));
        } finally {
            clearTimeout(timer);
            if (inflight === controller) {
                inflight = null;
            }
        }
    }

    function statusPayloadFromPanel() {
        const code = panel.getAttribute("data-status-code");
        if (!code) {
            return null;
        }
        const payload = {
            ok: panel.classList.contains("ok"),
            code: code,
            message: panel.getAttribute("data-status-message") || "",
        };
        panel.getAttributeNames().forEach(function (name) {
            if (name.startsWith("data-status-") && name !== "data-status-code" && name !== "data-status-message") {
                const key = name.slice("data-status-".length).replace(/-/g, "_");
                payload[key] = panel.getAttribute(name);
            }
        });
        return payload;
    }

    function translateInitialPanel() {
        const payload = statusPayloadFromPanel();
        if (!payload) {
            return;
        }
        if (payload.code === "checking_model_availability") {
            panel.textContent = t("checking_model_availability");
            panel.classList.remove("ok", "error");
            analyzeBtn.disabled = true;
            return;
        }
        setStatus(payload.ok, apiErrorMessage(payload));
    }

    select.addEventListener("change", function () {
        checkModel(select.value);
    });

    panel.addEventListener("click", function () {
        if (select.value) {
            checkModel(select.value, true);
        }
    });

    document.addEventListener("iiv-lang-changed", function () {
        if (select.value) {
            checkModel(select.value);
        } else {
            setStatus(false, t("select_model_to_check"));
        }
    });

    translateInitialPanel();
    if (select.value) {
        checkModel(select.value);
    }
})();
