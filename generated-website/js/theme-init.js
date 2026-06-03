(function () {
  'use strict';

  try {
    var theme = window.raehuPreferences && window.raehuPreferences.get('theme');
    document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');
  } catch (error) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();
