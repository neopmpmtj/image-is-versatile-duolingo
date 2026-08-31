(function () {
    const select = document.getElementById("pref-language");
    if (!select) {
        return;
    }

    function syncUiLangField() {
        const langInput = document.getElementById("id_ui_lang");
        if (langInput) {
            langInput.value = currentLang();
        }
    }

    select.value = currentLang();
    syncUiLangField();
    document.addEventListener("iiv-lang-changed", syncUiLangField);
    document.addEventListener("submit", syncUiLangField);
    select.addEventListener("change", function () {
        safeSet(LANG_KEY, normalizeLang(select.value));
        document.dispatchEvent(new CustomEvent("iiv-lang-changed"));
    });
})();
