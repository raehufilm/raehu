(function () {
  'use strict';

  var lazyVideos = Array.prototype.slice.call(document.querySelectorAll('video[data-lazy-video]'));
  var responsiveVideos = Array.prototype.slice.call(document.querySelectorAll('video[data-responsive-video]'));
  if (!lazyVideos.length && !responsiveVideos.length) return;
  var viewportMargin = 400;
  var ticking = false;
  var responsiveTicking = false;
  var scheduleFrame = window.requestAnimationFrame || function (callback) {
    return window.setTimeout(callback, 16);
  };

  function responsiveVideoVariants(video) {
    var variants = [];
    Array.prototype.slice.call(video.attributes).forEach(function (attribute) {
      var match = attribute.name.match(/^data-src-(\d+)$/);
      if (!match || !attribute.value) return;
      variants.push({
        width: parseInt(match[1], 10),
        src: attribute.value
      });
    });

    variants.sort(function (a, b) {
      return a.width - b.width;
    });

    return variants;
  }

  function responsiveVideoChoice(video) {
    var variants = responsiveVideoVariants(video);
    if (!variants.length) {
      var fallback = video.getAttribute('data-src');
      return fallback ? { width: 0, src: fallback } : null;
    }

    var rect = video.getBoundingClientRect();
    var cssWidth = rect.width || video.clientWidth || 0;

    if (!cssWidth) return null;

    for (var i = 0; i < variants.length; i++) {
      if (variants[i].width >= cssWidth) return variants[i];
    }

    return variants[variants.length - 1];
  }

  function responsiveVideoSource(video) {
    var choice = responsiveVideoChoice(video);
    return choice && choice.src;
  }

  function setVideoSource(video, source, variantWidth, allowDowngrade) {
    var currentSrc = video.getAttribute('src');
    var currentWidth = parseInt(video.dataset.responsiveWidth || '0', 10) || 0;

    if (!source || currentSrc === source) return false;
    if (
      currentSrc &&
      currentWidth &&
      variantWidth &&
      variantWidth <= currentWidth &&
      !allowDowngrade
    ) {
      return false;
    }

    video.setAttribute('src', source);
    if (variantWidth) video.dataset.responsiveWidth = String(variantWidth);
    video.load();
    return true;
  }

  function activateResponsiveVideo(video) {
    var choice = responsiveVideoChoice(video);
    if (!choice) return false;
    return setVideoSource(video, choice.src, choice.width, false);
  }

  function activateVideo(video) {
    if (video.dataset.lazyLoaded === 'true') return true;

    var choice = responsiveVideoChoice(video);
    if (!choice) return false;
    if (!video.getAttribute('src')) {
      setVideoSource(video, choice.src, choice.width, true);
    }

    video.dataset.lazyLoaded = 'true';
    return true;
  }

  function isNearViewport(video) {
    var rect = video.getBoundingClientRect();
    var height = window.innerHeight || document.documentElement.clientHeight;
    return rect.bottom >= -viewportMargin && rect.top <= height + viewportMargin;
  }

  function activateVisibleVideos() {
    lazyVideos.forEach(function (video) {
      if (video.dataset.lazyLoaded === 'true') return;
      if (isNearViewport(video)) activateVideo(video);
    });
    ticking = false;
  }

  function requestVisibleCheck() {
    if (ticking) return;
    ticking = true;
    scheduleFrame(activateVisibleVideos);
  }

  function activateResponsiveVideos() {
    responsiveVideos.forEach(activateResponsiveVideo);
    responsiveTicking = false;
  }

  function requestResponsiveVideoCheck() {
    if (responsiveTicking) return;
    responsiveTicking = true;
    scheduleFrame(activateResponsiveVideos);
  }

  if (responsiveVideos.length) {
    requestResponsiveVideoCheck();
    window.addEventListener('resize', function () {
      requestResponsiveVideoCheck();
      window.setTimeout(requestResponsiveVideoCheck, 150);
    });
    window.addEventListener('load', requestResponsiveVideoCheck);
    document.addEventListener('portfolio-grid:layout', requestResponsiveVideoCheck);
    window.setTimeout(requestResponsiveVideoCheck, 100);
    window.setTimeout(requestResponsiveVideoCheck, 500);
  }

  if (!lazyVideos.length) return;

  if (!('IntersectionObserver' in window)) {
    activateVisibleVideos();
    window.addEventListener('scroll', requestVisibleCheck, { passive: true });
    window.addEventListener('resize', requestVisibleCheck);
    window.addEventListener('load', requestVisibleCheck);
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      if (activateVideo(entry.target)) {
        observer.unobserve(entry.target);
      }
    });
  }, {
    rootMargin: '400px 0px',
    threshold: 0.01
  });

  lazyVideos.forEach(function (video) {
    observer.observe(video);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', requestVisibleCheck);
  } else {
    requestVisibleCheck();
  }
  window.addEventListener('scroll', requestVisibleCheck, { passive: true });
  window.addEventListener('resize', requestVisibleCheck);
  window.addEventListener('load', requestVisibleCheck);
  window.setTimeout(requestVisibleCheck, 100);
  window.setTimeout(requestVisibleCheck, 500);
  window.setTimeout(requestVisibleCheck, 1200);
})();
