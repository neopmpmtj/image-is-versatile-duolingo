const LANG_KEY = "iiv-lang";

function safeGet(key, fallback) {
    try {
        return localStorage.getItem(key) || fallback;
    } catch (error) {
        return fallback;
    }
}

function safeSet(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        /* storage blocked */
    }
}

function normalizeLang(raw) {
    if (raw && String(raw).toLowerCase().startsWith("pt")) {
        return "pt";
    }
    return "en";
}

function currentLang() {
    return normalizeLang(safeGet(LANG_KEY, "en"));
}

function localeTag() {
    return currentLang() === "pt" ? "pt-PT" : "en-GB";
}

function t(key, vars) {
    const dict = APP_I18N[currentLang()] || APP_I18N.en;
    let text = dict[key] || APP_I18N.en[key] || key;
    if (vars) {
        Object.entries(vars).forEach(([name, value]) => {
            text = text.replaceAll(`{${name}}`, String(value));
        });
    }
    return text;
}

function apiErrorMessage(payload) {
    const fallback = payload.message || payload.error || t("errorGeneric");
    const code = payload.code;
    if (!code) {
        return fallback;
    }
    const localized = t(code, payload);
    if (!localized || localized === code) {
        return fallback;
    }
    if (!localized.includes("{")) {
        if (currentLang() === "en" && payload.message) {
            return payload.message;
        }
        return localized;
    }
    return t(code, payload);
}

function formatDateTime(isoString) {
    if (!isoString) {
        return "";
    }
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) {
        return isoString;
    }
    return date.toLocaleString(localeTag(), {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function applyDateTimeNodes() {
    document.querySelectorAll("[data-datetime]").forEach((node) => {
        const iso = node.getAttribute("data-datetime");
        const formatted = formatDateTime(iso);
        if (formatted) {
            node.textContent = formatted;
        }
    });
}

function applyPresetOptionLabels() {
    document.querySelectorAll("option[data-i18n]").forEach((node) => {
        node.textContent = t(node.getAttribute("data-i18n"));
    });
}

function applyFlashMessages() {
    document.querySelectorAll("[data-flash-msg]").forEach((node) => {
        const raw = node.getAttribute("data-flash-msg");
        let code = raw;
        let vars = {};
        try {
            const parsed = JSON.parse(raw);
            code = parsed.code || raw;
            vars = parsed.vars || {};
        } catch (error) {
            /* plain code string */
        }
        node.textContent = t(code, vars);
    });
}

function applyStaticI18n() {
    const lang = currentLang();
    document.documentElement.lang = lang === "pt" ? "pt-PT" : "en";

    const titleKey = document.body.getAttribute("data-i18n-title");
    if (titleKey) {
        document.title = t(titleKey);
    }

    document.querySelectorAll("[data-i18n]").forEach((node) => {
        if (node.tagName === "OPTION") {
            return;
        }
        node.textContent = t(node.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
        node.setAttribute("placeholder", t(node.getAttribute("data-i18n-placeholder")));
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
        node.setAttribute("aria-label", t(node.getAttribute("data-i18n-aria")));
    });
    document.querySelectorAll("[data-i18n-html]").forEach((node) => {
        node.innerHTML = t(node.getAttribute("data-i18n-html"));
    });

    applyPresetOptionLabels();
    applyDateTimeNodes();
    applyFlashMessages();
}

document.addEventListener("DOMContentLoaded", applyStaticI18n);
document.addEventListener("iiv-lang-changed", applyStaticI18n);
