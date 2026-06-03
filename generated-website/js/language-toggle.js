(function () {
  'use strict';

  var STORAGE_KEY = 'raehu-language';
  var root = document.documentElement;
  var LANGUAGE_LABELS = {
    en: 'EN',
    cn: 'CN',
    es: 'ES',
  };

  function normalizeLanguage(value) {
    return value === 'cn' || value === 'es' ? value : 'en';
  }

  function activeLanguage() {
    return normalizeLanguage(root.getAttribute('data-language'));
  }

  function persistLanguage(language) {
    if (window.raehuPreferences) {
      window.raehuPreferences.set('language', language);
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, language);
    } catch (error) {
      // Ignore storage failures; the language switch should still work for this page.
    }
  }

  function closeMenus() {
    document.querySelectorAll('[data-language-menu]').forEach(function (menu) {
      menu.classList.remove('is-open');
      var toggle = menu.querySelector('[data-language-toggle]');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    });
  }

  function updateControls(language) {
    var label = LANGUAGE_LABELS[language] || LANGUAGE_LABELS.en;

    document.querySelectorAll('[data-language-current]').forEach(function (current) {
      current.textContent = label;
    });

    document.querySelectorAll('[data-language-option]').forEach(function (option) {
      var isSelected = normalizeLanguage(option.getAttribute('data-language-option')) === language;
      option.setAttribute(
        'aria-selected',
        isSelected ? 'true' : 'false'
      );
      option.hidden = isSelected;
    });
  }

  function revealSelectedLanguageContent(language) {
    document.querySelectorAll('[data-language-content="' + language + '"].fade-up').forEach(function (element) {
      element.classList.add('visible');
    });
  }

  function setLanguage(language, shouldPersist) {
    language = normalizeLanguage(language);
    root.setAttribute('data-language', language);
    root.setAttribute('lang', language === 'cn' ? 'zh-Hans' : language);
    updateControls(language);
    if (shouldPersist) revealSelectedLanguageContent(language);
    if (shouldPersist) persistLanguage(language);
  }

  setLanguage(activeLanguage(), false);

  document.querySelectorAll('[data-language-menu]').forEach(function (menu) {
    var toggle = menu.querySelector('[data-language-toggle]');
    if (!toggle) return;

    toggle.addEventListener('click', function (event) {
      event.stopPropagation();
      var willOpen = !menu.classList.contains('is-open');
      closeMenus();
      menu.classList.toggle('is-open', willOpen);
      toggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
  });

  document.querySelectorAll('[data-language-option]').forEach(function (option) {
    option.addEventListener('click', function (event) {
      event.stopPropagation();
      setLanguage(option.getAttribute('data-language-option'), true);
      closeMenus();
    });
  });

  document.addEventListener('click', closeMenus);
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeMenus();
  });
})();
