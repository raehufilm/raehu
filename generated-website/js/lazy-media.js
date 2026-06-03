(function () {
  'use strict';

  var lazyVideos = Array.prototype.slice.call(document.querySelectorAll('video[data-lazy-video]'));
  if (!lazyVideos.length) return;

  function activateVideo(video) {
    if (video.dataset.lazyLoaded === 'true') return;

    var source = video.getAttribute('data-src');
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
