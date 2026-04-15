// Grok News Widget — инжектируется в Homepage
(function () {
  function waitForElement(selector, callback, maxWait) {
    var start = Date.now();
    var interval = setInterval(function () {
      var el = document.querySelector(selector);
      if (el) {
        clearInterval(interval);
        callback(el);
      } else if (Date.now() - start > (maxWait || 10000)) {
        clearInterval(interval);
      }
    }, 200);
  }

  function injectNewsWidget(container) {
    var widget = document.createElement('div');
    widget.id = 'grok-news-widget';
    widget.innerHTML =
      '<div id="grok-news-header">' +
        '<span id="grok-news-title">🗞 Сводка новостей</span>' +
        '<button id="grok-news-btn" onclick="window._grokLoad()">↻ Обновить сводку</button>' +
      '</div>' +
      '<div id="grok-news-meta"></div>' +
      '<div id="grok-news-content" class="loading">Нажмите «Обновить сводку» для загрузки</div>';

    // Insert before the services section
    container.parentNode.insertBefore(widget, container);

    window._grokLoad = function () {
      var content = document.getElementById('grok-news-content');
      var meta = document.getElementById('grok-news-meta');
      content.className = 'loading';
      content.textContent = '⏳ Загружаю сводку...';
      meta.textContent = '';

      fetch('/grok-news/summary', { method: 'POST' })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.error) throw new Error(d.error);
          content.className = '';
          content.textContent = d.summary;
          meta.textContent = 'Обновлено: ' + new Date().toLocaleTimeString('ru-RU');
        })
        .catch(function (e) {
          content.className = 'error';
          content.textContent = 'Ошибка загрузки: ' + e.message;
        });
    };
  }

  // Wait for the services list to appear, then inject widget before it
  waitForElement('#services-list', function (el) {
    injectNewsWidget(el);
  }, 15000);

  // Fallback: try finding main section
  waitForElement('main section', function (el) {
    if (!document.getElementById('grok-news-widget')) {
      injectNewsWidget(el);
    }
  }, 15000);
})();
