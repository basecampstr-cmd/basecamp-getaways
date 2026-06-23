(function () {
  // --- Sticky nav state ---
  var nav = document.getElementById('nav');
  var hasHero = !!document.querySelector('.hero');
  function onScroll() {
    if (!nav) return;
    if (!hasHero || window.scrollY > 40) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll); onScroll();

  // --- Mobile menu ---
  var burger = document.getElementById('burger');
  var links = document.getElementById('navlinks');
  if (burger && links) burger.addEventListener('click', function () { links.classList.toggle('open'); });

  // --- Hero slideshow ---
  var hero = document.querySelector('.hero');
  var slides = document.querySelectorAll('.hero-slide');
  if (hero && slides.length > 1) {
    var dots = document.createElement('div');
    dots.className = 'hero-dots';
    slides.forEach(function (s, i) {
      var d = document.createElement('span');
      if (i === 0) d.className = 'on';
      d.addEventListener('click', function () { go(i); });
      dots.appendChild(d);
    });
    hero.appendChild(dots);
    var hi = 0, timer;
    function go(n) {
      slides[hi].classList.remove('active');
      dots.children[hi].classList.remove('on');
      hi = (n + slides.length) % slides.length;
      slides[hi].classList.add('active');
      dots.children[hi].classList.add('on');
      restart();
    }
    function restart() { clearInterval(timer); timer = setInterval(function () { go(hi + 1); }, 5500); }
    restart();
  }

  // --- Collection horizontal scrollers ---
  document.querySelectorAll('.scroller').forEach(function (sc) {
    var track = sc.querySelector('.scroll-track');
    var prev = sc.querySelector('.prev'), next = sc.querySelector('.next');
    if (!track) return;
    function amt() { return Math.max(track.clientWidth * 0.85, 370); }
    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -amt(), behavior: 'smooth' }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: amt(), behavior: 'smooth' }); });
    function upd() {
      var max = track.scrollWidth - track.clientWidth - 4;
      if (prev) prev.style.display = track.scrollLeft > 4 ? 'flex' : 'none';
      if (next) next.style.display = track.scrollLeft < max ? 'flex' : 'none';
    }
    track.addEventListener('scroll', upd); window.addEventListener('resize', upd); upd();
  });

  // --- Search / filter the All Homes grid ---
  var go = document.getElementById('s-go');
  var grid = document.getElementById('allGrid');
  if (go && grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
    var noRes = document.getElementById('noResults');
    function runSearch() {
      var region = (document.getElementById('s-region') || {}).value || '';
      var guests = parseInt((document.getElementById('s-guests') || {}).value || '0', 10) || 0;
      var shown = 0;
      cards.forEach(function (c) {
        var okR = !region || c.getAttribute('data-region') === region;
        var okG = !guests || parseInt(c.getAttribute('data-guests') || '0', 10) >= guests;
        var show = okR && okG;
        c.style.display = show ? '' : 'none';
        if (show) shown++;
      });
      if (noRes) noRes.hidden = shown !== 0;
      var target = document.getElementById('properties');
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    }
    go.addEventListener('click', runSearch);
    var clear = document.getElementById('clearSearch');
    if (clear) clear.addEventListener('click', function () {
      cards.forEach(function (c) { c.style.display = ''; });
      if (noRes) noRes.hidden = true;
      var r = document.getElementById('s-region'), g = document.getElementById('s-guests');
      if (r) r.value = ''; if (g) g.value = '';
    });
  }

  // --- Read more (property description) ---
  var prose = document.getElementById('prose');
  var rm = document.getElementById('readmore');
  if (prose && rm) {
    if (prose.scrollHeight <= 360) { prose.classList.remove('clamp'); rm.style.display = 'none'; }
    rm.addEventListener('click', function () {
      prose.classList.toggle('open');
      rm.textContent = prose.classList.contains('open') ? 'Show less ↑' : 'Read more ↓';
    });
  }

  // --- Photo gallery / lightbox ---
  var gEl = document.querySelector('.gallery');
  if (gEl) {
    var photos = [];
    try { photos = JSON.parse(gEl.getAttribute('data-gallery')) || []; } catch (e) {}
    var lb = document.getElementById('lightbox');
    var lbImg = document.getElementById('lbImg');
    var lbCount = document.getElementById('lbCount');
    var idx = 0;
    function show(i) {
      if (!photos.length) return;
      idx = (i + photos.length) % photos.length;
      lbImg.src = photos[idx];
      lbCount.textContent = (idx + 1) + ' / ' + photos.length;
    }
    function open(i) { if (!lb) return; lb.hidden = false; show(i); document.body.style.overflow = 'hidden'; }
    function close() { if (!lb) return; lb.hidden = true; document.body.style.overflow = ''; }
    var showAll = document.getElementById('showAll');
    if (showAll) showAll.addEventListener('click', function () { open(0); });
    var mainImg = gEl.querySelector('.g-main img');
    if (mainImg) mainImg.addEventListener('click', function () { open(0); });
    var thumbs = gEl.querySelectorAll('.g-thumb img');
    thumbs.forEach(function (t, i) { t.addEventListener('click', function () { open(i + 1); }); });
    var c = document.getElementById('lbClose'), pv = document.getElementById('lbPrev'), nx = document.getElementById('lbNext');
    if (c) c.addEventListener('click', close);
    if (pv) pv.addEventListener('click', function () { show(idx - 1); });
    if (nx) nx.addEventListener('click', function () { show(idx + 1); });
    if (lb) lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (lb && lb.hidden) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  // --- Booking widget (Hospitable direct) ---
  var card = document.getElementById('bookCard');
  var mount = document.getElementById('booking-widget-mount');
  if (card && mount) {
    var slug = card.getAttribute('data-slug');
    var cfg = (window.SITE_CONFIG && window.SITE_CONFIG.widgets) || {};
    var src = (cfg[slug] || '').trim();
    if (src && /^https?:\/\//.test(src)) {
      var iframe = document.createElement('iframe');
      iframe.id = 'booking-iframe';
      iframe.src = src;
      iframe.setAttribute('title', 'Book this home');
      mount.appendChild(iframe);
      // Hospitable posts iframe height for dynamic resizing
      window.addEventListener('message', function (event) {
        if (event.data && event.data.iframeHeight) {
          iframe.style.height = event.data.iframeHeight + 'px';
        }
      });
    } else {
      var fb = (window.SITE_CONFIG && window.SITE_CONFIG.fallbackBookingUrl || '').trim();
      var href = fb || '#';
      mount.innerHTML =
        '<div class="book-fallback">' +
          '<div class="fb-line"><span>Check‑in</span><span>Select dates</span></div>' +
          '<div class="fb-line"><span>Check‑out</span><span>Select dates</span></div>' +
          '<div class="fb-line"><span>Guests</span><span>Add guests</span></div>' +
          '<a class="btn" href="' + href + '"' + (fb ? ' target="_blank" rel="noopener"' : '') + '>Check availability</a>' +
          '<p class="book-note">Secure checkout powered by Hospitable.</p>' +
        '</div>';
    }
  }
})();
