(function () {
    const overlay = document.getElementById("busy-overlay");
    if (!overlay) {
        return;
    }
    const messageEl = overlay.querySelector(".busy-message");
    const cancelBtn = document.getElementById("busy-cancel");
    const MAX_VISIBLE_MS = 185000;
    let disabledSource = null;
    let hideTimer = null;

    function hideBusy() {
        overlay.classList.remove("is-visible");
        overlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("is-busy");
        if (disabledSource && "disabled" in disabledSource) {
            disabledSource.disabled = false;
        }
        disabledSource = null;
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
    }

    function showBusy(i18nKey, source) {
        if (overlay.classList.contains("is-visible")) {
            return;
        }
        if (i18nKey) {
            messageEl.textContent = t(i18nKey);
        }
        overlay.classList.add("is-visible");
        overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("is-busy");
        if (source && "disabled" in source) {
            source.disabled = true;
            disabledSource = source;
        }
        hideTimer = setTimeout(hideBusy, MAX_VISIBLE_MS);
    }

    document.addEventListener("submit", function (event) {
        const form = event.target;
        if (!form || !form.hasAttribute("data-wait-i18n")) {
            return;
        }
        showBusy(form.getAttribute("data-wait-i18n"), event.submitter);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("is-visible")) {
            hideBusy();
        }
    });

    window.addEventListener("pageshow", function () {
        if (overlay.classList.contains("is-visible")) {
            hideBusy();
        }
    });

    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) {
            hideBusy();
        }
    });

    if (cancelBtn) {
        cancelBtn.addEventListener("click", hideBusy);
    }
})();
