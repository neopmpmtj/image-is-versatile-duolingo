(function () {
    const overlay = document.getElementById("busy-overlay");
    if (!overlay) {
        return;
    }
    const messageEl = overlay.querySelector(".busy-message");
    const cancelBtn = document.getElementById("busy-cancel");
    const MAX_VISIBLE_MS = 185000;
    let hideTimer = null;
    const submittedForms = new WeakSet();

    function lockSubmitControls(form) {
        if (!form) {
            return;
        }
        form.setAttribute("data-busy-submitted", "1");
        form.querySelectorAll("button[type=submit], input[type=submit], button:not([type])").forEach(function (el) {
            el.disabled = true;
            el.setAttribute("data-busy-disabled", "1");
        });
    }

    function unlockSubmitControls(form) {
        if (!form) {
            return;
        }
        form.removeAttribute("data-busy-submitted");
        form.querySelectorAll("[data-busy-disabled]").forEach(function (el) {
            el.disabled = false;
            el.removeAttribute("data-busy-disabled");
        });
    }

    function hideBusy() {
        overlay.classList.remove("is-visible");
        overlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("is-busy");
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
    }

    function showBusy(i18nKey, form) {
        if (overlay.classList.contains("is-visible")) {
            return;
        }
        if (i18nKey) {
            messageEl.textContent = t(i18nKey);
        }
        overlay.classList.add("is-visible");
        overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("is-busy");
        lockSubmitControls(form);
        hideTimer = setTimeout(hideBusy, MAX_VISIBLE_MS);
    }

    document.addEventListener("submit", function (event) {
        const form = event.target;
        if (!form || !form.hasAttribute("data-wait-i18n")) {
            return;
        }
        if (submittedForms.has(form) || form.getAttribute("data-busy-submitted") === "1") {
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        submittedForms.add(form);
        showBusy(form.getAttribute("data-wait-i18n"), form);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("is-visible")) {
            hideBusy();
        }
    });

    window.addEventListener("pageshow", function (event) {
        if (overlay.classList.contains("is-visible")) {
            hideBusy();
        }
        if (event.persisted) {
            document.querySelectorAll("form[data-wait-i18n]").forEach(function (form) {
                submittedForms.delete(form);
                unlockSubmitControls(form);
            });
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
