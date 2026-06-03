/**
 * Makes directory-style links work when previewing generated pages via file://.
 *
 * Browsers do not resolve fragments on local directory links the same way a
 * web server does. For local previews only, rewrite same-site relative links
 * that point at directories so they explicitly target index.html.
 */
(function () {
  'use strict';

  if (window.location.protocol !== 'file:') return;

  function explicitIndexHref(href) {
    if (!href || href.charAt(0) === '#') return href;
    if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.indexOf('//') === 0) return href;

    var hashIndex = href.indexOf('#');
    var path = hashIndex >= 0 ? href.slice(0, hashIndex) : href;
    var hash = hashIndex >= 0 ? href.slice(hashIndex) : '';

    if (!path || !path.endsWith('/')) return href;
    return path + 'index.html' + hash;
  }

  document.querySelectorAll('a[href]').forEach(function (link) {
    var href = link.getAttribute('href');
    var nextHref = explicitIndexHref(href);
    if (nextHref !== href) {
      link.setAttribute('href', nextHref);
    }
  });
})();
