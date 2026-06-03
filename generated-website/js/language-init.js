(function () {
  'use strict';

  try {
    var language = window.raehuPreferences
      ? window.raehuPreferences.get('language')
      : window.localStorage.getItem('raehu-language');
    language = language === 'cn' || language === 'es' ? language : 'en';
    document.documentElement.setAttribute('data-language', language);
    document.documentElement.setAttribute(
      'lang',
      language === 'cn' ? 'zh-Hans' : language
    );
  } catch (error) {
    document.documentElement.setAttribute('data-language', 'en');
    document.documentElement.setAttribute('lang', 'en');
  }
})();
