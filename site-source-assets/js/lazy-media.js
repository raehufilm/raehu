(function () {
  'use strict';

  var lazyVideos = Array.prototype.slice.call(document.querySelectorAll('video[data-lazy-video]'));
  if (!lazyVideos.length) return;

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

    if (!targetWidth) return variants[variants.length - 1].src;

    for (var i = 0; i < variants.length; i++) {
      if (variants[i].width >= targetWidth) return variants[i].src;
    }

    return variants[variants.length - 1].src;
  }

  function activateVideo(video) {
    if (video.dataset.lazyLoaded === 'true') return;

    var source = responsiveVideoSource(video);
    if (source && !video.getAttribute('src')) {
      video.setAttribute('src', source);
      video.load();
    }

    video.dataset.lazyLoaded = 'true';

    if (video.getAttribute('data-autoplay') === 'true') {
      var play = video.play && video.play();
      if (play && play.catch) play.catch(function () {});
    }
  }

  if (!('IntersectionObserver' in window)) {
    lazyVideos.forEach(activateVideo);
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      activateVideo(entry.target);
      observer.unobserve(entry.target);
    });
  }, {
    rootMargin: '400px 0px',
    threshold: 0.01
  });

  lazyVideos.forEach(function (video) {
    observer.observe(video);
  });
})();
