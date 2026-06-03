(function () {
  'use strict';

  var STORAGE_KEY = 'raehu-theme';
  var root = document.documentElement;

  function storedTheme() {
    if (window.raehuPreferences) {
      var stored = window.raehuPreferences.get('theme');
      return stored === 'light' || stored === 'dark' ? stored : null;
    }

    try {
      var value = window.localStorage.getItem(STORAGE_KEY);
      return value === 'light' || value === 'dark' ? value : null;
    } catch (error) {
      return null;
    }
  }

  function activeTheme() {
    return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function persistTheme(theme) {
    if (window.raehuPreferences) {
      window.raehuPreferences.set('theme', theme);
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // Ignore storage failures; the toggle should still work for this page.
    }
  }

  function updateButtons(theme) {
    var nextTheme = theme === 'light' ? 'dark' : 'light';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      button.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
      button.setAttribute('aria-label', 'Switch to ' + nextTheme + ' mode');
    });
  }

  function setTheme(theme, shouldPersist) {
    root.setAttribute('data-theme', theme);
    if (shouldPersist) persistTheme(theme);
    updateButtons(theme);
  }

  setTheme(storedTheme() || activeTheme(), false);

  document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
    button.addEventListener('click', function () {
      var nextTheme = activeTheme() === 'light' ? 'dark' : 'light';
      setTheme(nextTheme, true);
    });
  });
})();
