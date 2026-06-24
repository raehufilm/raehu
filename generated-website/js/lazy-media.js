(function () {
  'use strict';

  var lazyVideos = Array.prototype.slice.call(document.querySelectorAll('video[data-lazy-video]'));
  if (!lazyVideos.length) return;
  var viewportMargin = 400;
  var ticking = false;
  var scheduleFrame = window.requestAnimationFrame || function (callback) {
    return window.setTimeout(callback, 16);
  };

  function responsiveVideoSource(video) {
    var variants = [];
    Array.prototype.slice.call(video.attributes).forEach(function (attribute) {
      var match = attribute.name.match(/^data-src-(\d+)$/);
      if (!match || !attribute.value) return;
      variants.push({
        width: parseInt(match[1], 10),
        src: attribute.value
      });
    });

    if (!variants.length) return video.getAttribute('data-src');

    variants.sort(function (a, b) {
      return a.width - b.width;
    });

    var rect = video.getBoundingClientRect();
    var cssWidth = rect.width || video.clientWidth || 0;
    var targetWidth = cssWidth * (window.devicePixelRatio || 1);

    if (!targetWidth) return null;

    for (var i = 0; i < variants.length; i++) {
      if (variants[i].width >= targetWidth) return variants[i].src;
    }

    return variants[variants.length - 1].src;
  }

  function activateVideo(video) {
    if (video.dataset.lazyLoaded === 'true') return true;

    var source = responsiveVideoSource(video);
    if (!source) return false;
    if (source && !video.getAttribute('src')) {
      video.setAttribute('src', source);
      if (video.getAttribute('data-autoplay') === 'true') {
        video.autoplay = true;
        video.setAttribute('autoplay', '');
      }
      video.load();
    }

    video.dataset.lazyLoaded = 'true';
    playVideo(video);
    return true;
  }

  function playVideo(video) {
    if (video.getAttribute('data-autoplay') === 'true') {
      var play = video.play && video.play();
      if (play && play.catch) play.catch(function () {});
    }
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

  lazyVideos.forEach(function (video) {
    video.addEventListener('loadedmetadata', function () {
      playVideo(video);
    });
    video.addEventListener('canplay', function () {
      playVideo(video);
    });
  });

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
