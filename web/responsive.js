(function () {
  'use strict';

  var mobileQuery = window.matchMedia('(max-width: 960px)');

  function initNavigation(nav, index) {
    var inner = nav.querySelector('.nav-in');
    var links = nav.querySelector('.nav-links');
    if (!inner || !links || nav.getAttribute('data-responsive-ready') === 'true') return;

    nav.setAttribute('data-responsive-ready', 'true');
    if (!links.id) links.id = 'site-navigation-' + index;

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'nav-toggle';
    toggle.setAttribute('aria-label', '打开网站菜单');
    toggle.setAttribute('aria-controls', links.id);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.innerHTML = '<span class="nav-toggle-box" aria-hidden="true"><span class="nav-toggle-line"></span><span class="nav-toggle-line"></span><span class="nav-toggle-line"></span></span>';
    inner.insertBefore(toggle, links);

    var backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'nav-backdrop';
    backdrop.setAttribute('aria-label', '关闭网站菜单');
    document.body.appendChild(backdrop);

    function isOpen() {
      return nav.getAttribute('data-menu-open') === 'true';
    }

    function setOpen(open, returnFocus) {
      open = Boolean(open && mobileQuery.matches);
      nav.setAttribute('data-menu-open', open ? 'true' : 'false');
      backdrop.setAttribute('data-open', open ? 'true' : 'false');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? '关闭网站菜单' : '打开网站菜单');
      links.setAttribute('aria-hidden', mobileQuery.matches && !open ? 'true' : 'false');
      document.body.classList.toggle('site-menu-open', open);
      if (!open && returnFocus) toggle.focus();
    }

    function syncBreakpoint() {
      setOpen(false, false);
      if (!mobileQuery.matches) links.removeAttribute('aria-hidden');
    }

    toggle.addEventListener('click', function () {
      setOpen(!isOpen(), false);
    });
    backdrop.addEventListener('click', function () {
      setOpen(false, true);
    });
    links.addEventListener('click', function (event) {
      if (event.target.closest && event.target.closest('a')) setOpen(false, false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && isOpen()) setOpen(false, true);
    });

    if (mobileQuery.addEventListener) mobileQuery.addEventListener('change', syncBreakpoint);
    else mobileQuery.addListener(syncBreakpoint);

    syncBreakpoint();
  }

  function init() {
    var navs = document.querySelectorAll('body > nav, body > header + nav');
    for (var i = 0; i < navs.length; i += 1) initNavigation(navs[i], i + 1);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}());
