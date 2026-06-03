(function () {
  'use strict';

  var STORAGE_KEY = 'raehu-preferences';
  var WINDOW_NAME_PREFIX = 'raehu-preferences:';
  var LEGACY_KEYS = {
    theme: 'raehu-theme',
    language: 'raehu-language'
  };

  function parseJson(value) {
    if (!value) return {};
    try {
      var parsed = JSON.parse(value);
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function readLocalPreferences() {
    try {
      return parseJson(window.localStorage.getItem(STORAGE_KEY));
    } catch (error) {
      return {};
    }
  }

  function writeLocalPreferences(preferences) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      // Ignore storage failures; window.name is still available in local previews.
    }
  }

  function readWindowPreferences() {
    if (!window.name || window.name.indexOf(WINDOW_NAME_PREFIX) !== 0) return {};
    try {
      return parseJson(decodeURIComponent(window.name.slice(WINDOW_NAME_PREFIX.length)));
    } catch (error) {
      return {};
    }
  }

  function writeWindowPreferences(preferences) {
    try {
      window.name = WINDOW_NAME_PREFIX + encodeURIComponent(JSON.stringify(preferences));
    } catch (error) {
      // Ignore unusual browser restrictions.
    }
  }

  function readLegacyPreference(name) {
    var key = LEGACY_KEYS[name];
    if (!key) return null;
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function getPreference(name) {
    var localPreferences = readLocalPreferences();
    if (localPreferences[name]) return localPreferences[name];

    var legacyValue = readLegacyPreference(name);
    if (legacyValue) return legacyValue;

    var windowPreferences = readWindowPreferences();
    return windowPreferences[name] || null;
  }

  function setPreference(name, value) {
    var localPreferences = readLocalPreferences();
    localPreferences[name] = value;
    writeLocalPreferences(localPreferences);

    var windowPreferences = readWindowPreferences();
    windowPreferences[name] = value;
    writeWindowPreferences(windowPreferences);

    var legacyKey = LEGACY_KEYS[name];
    if (legacyKey) {
      try {
        window.localStorage.setItem(legacyKey, value);
      } catch (error) {
        // Ignore storage failures; the shared preference object has already been updated.
      }
    }
  }

  window.raehuPreferences = {
    get: getPreference,
    set: setPreference
  };
})();
