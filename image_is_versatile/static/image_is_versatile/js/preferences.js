(function () {
    const select = document.getElementById("pref-language");
    if (!select) {
        return;
    }

    select.value = currentLang();
    select.addEventListener("change", function () {
        safeSet(LANG_KEY, normalizeLang(select.value));
        document.dispatchEvent(new CustomEvent("iiv-lang-changed"));
    });
})();
