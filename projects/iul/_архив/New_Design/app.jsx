/* global React, ReactDOM, Icons, IUL_DATA, DropZone, FileRow, Console, ToastContainer, SettingsModal, useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakToggle, TweakColor */

const { useState: useS, useEffect: useE, useRef: useR, useMemo, useCallback: useCb } = React;

// Pre-canned scenarios so the prototype can switch between meaningful states
// without the user having to actually drag files in.
const SCENARIOS = ['empty', 'loaded', 'processing', 'done'];

function nextStatus(s) {
  if (s === 'idle') return 'parsing';
  if (s === 'parsing') return 'processing';
  if (s === 'processing') return 'exporting';
  return 'done';
}

function App() {
  const tweakDefaults = /*EDITMODE-BEGIN*/{
    "theme": "dark",
    "accent": "#3b82f6",
    "scenario": "loaded",
    "consoleOpen": true,
    "showHint": false
  }/*EDITMODE-END*/;

  // URL params override the editmode defaults — used by Canvas.html artboards.
  const urlParams = new URLSearchParams(location.search);
  const overrides = {};
  if (urlParams.get('scenario')) overrides.scenario = urlParams.get('scenario');
  if (urlParams.get('theme')) overrides.theme = urlParams.get('theme');
  if (urlParams.get('accent')) overrides.accent = urlParams.get('accent');
  const initialModal = urlParams.get('modal');

  const [tweaks, setTweak] = useTweaks({ ...tweakDefaults, ...overrides });

  // Initial files come from scenario via the effect below; start empty so
  // the very first paint matches whatever scenario the tweak says.
  const initFiles = (() => {
    if (tweakDefaults.scenario === 'empty') return [];
    return IUL_DATA.SAMPLE_FILES.map((f) => ({ ...f }));
  })();
  const [files, setFiles] = useS(initFiles);
  const [logs, setLogs] = useS([
    { time: '14:01:58', level: 'info', msg: 'Добавлено 6 файлов в очередь' },
    { time: '14:01:58', level: 'info', msg: 'Шаблон загружен: ИУЛ_шаблон.xlsx' },
  ]);
  const [consoleOpen, setConsoleOpen] = useS(tweaks.consoleOpen);
  const [settingsOpen, setSettingsOpen] = useS(!!initialModal);
  const [settingsTab, setSettingsTab] = useS(initialModal || 'project');
  const [toasts, setToasts] = useS([]);
  const [processing, setProcessing] = useS(false);
  const [outFolder, setOutFolder] = useS('C:\\Users\\gor-r\\Documents\\ИУЛ\\out');
  const [revision, setRevision] = useS('1');

  // Sync theme & accent
  useE(() => {
    document.documentElement.setAttribute('data-theme', tweaks.theme);
    document.documentElement.style.setProperty('--accent', tweaks.accent);
    // derive a slightly lighter hover from accent
    document.documentElement.style.setProperty('--accent-hover', tweaks.accent);
  }, [tweaks.theme, tweaks.accent]);

  // Apply scenario when it changes
  useE(() => {
    applyScenario(tweaks.scenario);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tweaks.scenario]);

  // Toast helpers
  const pushToast = (t) => {
    const id = Math.random().toString(36).slice(2, 9);
    setToasts((prev) => [...prev, { id, ...t }]);
    setTimeout(() => closeToast(id), 4500);
  };
  const closeToast = (id) => {
    setToasts((prev) => prev.map((t) => t.id === id ? { ...t, leaving: true } : t));
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 250);
  };

  // Apply scenario presets (used by Tweaks panel)
  const applyScenario = (scn) => {
    const base = IUL_DATA.SAMPLE_FILES.map((f) => ({ ...f }));
    if (scn === 'empty') {
      setFiles([]);
      setLogs([]);
    } else if (scn === 'loaded') {
      setFiles(base);
      setLogs([
        { time: '14:01:58', level: 'info', msg: 'Добавлено 6 файлов в очередь' },
        { time: '14:01:58', level: 'info', msg: 'Шаблон загружен: ИУЛ_шаблон.xlsx' },
      ]);
    } else if (scn === 'processing') {
      setFiles(base.map((f, i) => ({
        ...f,
        status: i === 0 ? 'done' : i === 1 ? 'processing' : i === 2 ? 'parsing' : 'idle',
        progress: i === 1 ? 62 : i === 2 ? 18 : 0,
      })));
      setLogs(IUL_DATA.SAMPLE_LOG.slice(0, 6));
    } else if (scn === 'done') {
      setFiles(base.map((f, i) => ({
        ...f,
        status: i === 3 ? 'error' : i === 1 ? 'warning' : 'done',
        progress: 100,
        warnings: i === 1 ? 1 : i === 3 ? 2 : 0,
      })));
      setLogs(IUL_DATA.SAMPLE_LOG);
    }
  };

  // Add files (simulated drop)
  const onAddFiles = () => {
    if (files.length >= IUL_DATA.SAMPLE_FILES.length) {
      pushToast({
        kind: 'info',
        title: 'Очередь уже заполнена',
        msg: 'Демонстрационный набор содержит ' + IUL_DATA.SAMPLE_FILES.length + ' файлов.',
      });
      return;
    }
    const remaining = IUL_DATA.SAMPLE_FILES.slice(files.length);
    const next = [...files, ...remaining.slice(0, 3)];
    setFiles(next);
    setLogs((prev) => [
      ...prev,
      { time: nowStr(), level: 'info', msg: `Добавлено ${Math.min(3, remaining.length)} файлов в очередь` },
    ]);
    pushToast({
      kind: 'success',
      title: `Добавлено ${Math.min(3, remaining.length)} файлов`,
      msg: 'Готовы к обработке.',
    });
  };

  const removeFile = (id) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const clearFiles = () => {
    setFiles([]);
    setLogs([]);
    setTweak('scenario', 'empty');
    pushToast({ kind: 'info', title: 'Очередь очищена' });
  };

  // Run processing animation
  const runProcess = () => {
    if (files.length === 0 || processing) return;
    setProcessing(true);
    pushToast({ kind: 'info', title: 'Обработка запущена', msg: `${files.length} файлов в очереди` });
    setLogs((prev) => [...prev, { time: nowStr(), level: 'info', msg: `Запуск пакетной обработки · ${files.length} файлов` }]);

    let stepIdx = 0;
    const total = files.length;
    const tick = () => {
      setFiles((prev) => {
        const next = prev.map((f) => ({ ...f }));
        // advance one file at a time
        const i = Math.min(stepIdx, next.length - 1);
        const f = next[i];
        if (!f) return next;
        if (f.status === 'idle') {
          f.status = 'parsing';
          f.progress = 25;
          appendLog('info', `${f.name} · парсинг имени`);
        } else if (f.status === 'parsing') {
          f.status = 'processing';
          f.progress = 60;
          appendLog('success', `CRC32 рассчитан: ${f.crc}`);
        } else if (f.status === 'processing') {
          f.status = 'exporting';
          f.progress = 90;
          appendLog('info', `Excel: лист «${f.section}» заполнен`);
        } else if (f.status === 'exporting') {
          // simulate occasional warning/error
          if (i === 1) {
            f.status = 'warning';
            f.warnings = 1;
            appendLog('warn', `Подпись «Левченко А.И.» не найдена для ${f.section}`);
          } else if (i === 3) {
            f.status = 'error';
            f.warnings = 2;
            appendLog('error', `Не удалось извлечь дату из ${f.name}`);
          } else {
            f.status = 'done';
            appendLog('success', `Готово: ИУЛ_${f.section}.pdf`);
          }
          f.progress = 100;
          stepIdx++;
        }
        return next;
      });
      if (stepIdx < total) {
        setTimeout(tick, 700);
      } else {
        setProcessing(false);
        pushToast({
          kind: 'success',
          title: 'Обработка завершена',
          msg: `${total} файлов · 1 предупр. · 1 ошибка`,
        });
      }
    };
    setTimeout(tick, 400);
  };

  const appendLog = (level, msg) => {
    setLogs((prev) => [...prev, { time: nowStr(), level, msg }]);
  };

  // Stats
  const stats = useMemo(() => ({
    total: files.length,
    done: files.filter((f) => f.status === 'done').length,
    warn: files.filter((f) => f.status === 'warning').length,
    err: files.filter((f) => f.status === 'error').length,
  }), [files]);

  return (
    <div className="win11-frame">
      {/* Title bar */}
      <div className="titlebar">
        <div className="titlebar-title">
          <span className="dot"></span>
          ИУЛ — Создание информационно-удостоверяющих листов
        </div>
        <div className="win-controls">
          <button title="Свернуть"><Icons.Minimize size={11} sw={1.5} /></button>
          <button title="Развернуть"><Icons.Maximize size={10} sw={1.5} /></button>
          <button className="close" title="Закрыть"><Icons.X size={11} sw={1.5} /></button>
        </div>
      </div>

      {/* Top bar */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">ИУЛ</div>
          <div className="brand-meta">
            <div className="brand-title">Создание ИУЛ</div>
            <div className="brand-sub">проект 1605-2022 · ревизия {revision}</div>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="search-box">
            <Icons.Search size={13} />
            <input placeholder="Поиск по файлам, разделам…" />
          </div>
          <div style={{ width: 8 }}></div>
          <button
            className="icon-btn"
            title={tweaks.theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            onClick={() => setTweak('theme', tweaks.theme === 'dark' ? 'light' : 'dark')}
          >
            {tweaks.theme === 'dark' ? <Icons.Sun size={16} /> : <Icons.Moon size={16} />}
          </button>
          <button className="icon-btn" title="Уведомления">
            <Icons.Bell size={16} />
          </button>
          <button className="icon-btn" title="Настройки" onClick={() => setSettingsOpen(true)}>
            <Icons.Settings size={16} />
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="app-body">
        {/* Main pane */}
        <div className="main-pane">
          <div className="main-content scroll-area">
            <h1 className="page-title">Создание информационно-удостоверяющих листов</h1>
            <div className="page-sub">
              Загрузите PDF-файлы проектной документации — приложение распарсит имя,
              рассчитает CRC32, заполнит шаблон Excel и экспортирует результат.
            </div>

            {/* Drop zone */}
            <DropZone onAddFiles={onAddFiles} hasFiles={files.length > 0} />

            {/* File list section */}
            {files.length > 0 && (
              <>
                <div className="section-break">
                  <div className="section-label">
                    Очередь обработки
                    <span className="count-pill">{files.length}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-ghost" onClick={clearFiles}>
                      <Icons.Trash size={14} /> Очистить
                    </button>
                    <button className="btn btn-ghost">
                      <Icons.Filter size={14} /> Фильтр
                    </button>
                  </div>
                </div>

                <div className="file-list">
                  <div className="file-list-header">
                    <div>Файл</div>
                    <div>Раздел / Часть / Книга</div>
                    <div>Статус</div>
                    <div></div>
                  </div>
                  {files.map((f) => (
                    <FileRow key={f.id} file={f} onRemove={removeFile} />
                  ))}
                </div>

                {(stats.warn > 0 || stats.err > 0) && (
                  <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {stats.err > 0 && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '8px 12px', borderRadius: 8,
                        background: 'var(--red-soft)', color: 'var(--red)',
                        fontSize: 12.5, fontWeight: 500,
                      }}>
                        <Icons.AlertCircle size={14} />
                        {stats.err} файл{stats.err === 1 ? '' : 'а'} с ошибкой — ИУЛ для них не создан.
                      </div>
                    )}
                    {stats.warn > 0 && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '8px 12px', borderRadius: 8,
                        background: 'var(--amber-soft)', color: 'var(--amber)',
                        fontSize: 12.5, fontWeight: 500,
                      }}>
                        <Icons.AlertTriangle size={14} />
                        {stats.warn} предупреждение — проверьте журнал.
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {files.length === 0 && (
              <div style={{
                marginTop: 32, padding: 24,
                border: '1px solid var(--border)',
                borderRadius: 10, background: 'var(--bg-elev-1)',
                display: 'flex', alignItems: 'center', gap: 16,
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: 'var(--bg-elev-3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--accent)',
                }}>
                  <Icons.Sparkles size={18} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, color: 'var(--text-strong)', marginBottom: 2 }}>
                    Подсказка
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--text-mute)' }}>
                    Имена файлов должны соответствовать ГОСТ Р 21.1101.
                    Поддерживаемые шифры разделов: <span style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>АР · КР · ПЗУ · ИОС1–ИОС7</span>.
                  </div>
                </div>
                <button className="btn">
                  <Icons.FileText size={14} /> Открыть документацию
                </button>
              </div>
            )}
          </div>

          {/* Console */}
          <Console
            logs={logs}
            open={consoleOpen}
            onToggle={() => setConsoleOpen((o) => !o)}
          />
        </div>

        {/* Right action rail */}
        <aside className="action-rail">
          <div className="rail-section">
            <div className="rail-title">Параметры выгрузки</div>
            <div className="rail-field">
              <label className="rail-label">Папка результата</label>
              <div className="rail-input-row">
                <input
                  className="rail-input"
                  value={outFolder}
                  onChange={(e) => setOutFolder(e.target.value)}
                />
                <button className="icon-btn" title="Выбрать папку">
                  <Icons.FolderOpen size={15} />
                </button>
              </div>
            </div>
            <div className="rail-field">
              <label className="rail-label">Номер изменения</label>
              <div className="rail-input-row">
                <input
                  className="rail-input numeric"
                  value={revision}
                  onChange={(e) => setRevision(e.target.value)}
                />
                <span style={{ fontSize: 11.5, color: 'var(--text-faint)' }}>
                  следующий: {parseInt(revision || 0) + 1}
                </span>
              </div>
            </div>
          </div>

          <div className="rail-section">
            <div className="rail-title">Сводка</div>
            <div className="rail-stat-grid">
              <div className="stat-card">
                <div className="stat-card-value">{stats.total}</div>
                <div className="stat-card-label">в очереди</div>
              </div>
              <div className="stat-card success">
                <div className="stat-card-value">{stats.done}</div>
                <div className="stat-card-label">готово</div>
              </div>
              <div className="stat-card warn">
                <div className="stat-card-value">{stats.warn}</div>
                <div className="stat-card-label">предупр.</div>
              </div>
              <div className="stat-card err">
                <div className="stat-card-value">{stats.err}</div>
                <div className="stat-card-label">ошибки</div>
              </div>
            </div>
          </div>

          <div className="rail-section" style={{ flex: 1, minHeight: 0 }}>
            <div className="rail-title">Шаблон</div>
            <div style={{
              padding: '10px 12px',
              border: '1px solid var(--border)',
              borderRadius: 8,
              background: 'var(--bg-elev-2)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <div style={{
                width: 28, height: 32, borderRadius: 5,
                background: 'var(--green-soft)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--green)', fontSize: 9, fontFamily: 'var(--mono)', fontWeight: 600,
              }}>XLSX</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--text-strong)' }}>ИУЛ_шаблон.xlsx</div>
                <div style={{ fontSize: 11, color: 'var(--text-faint)', fontFamily: 'var(--mono)' }}>1.2 МБ · 4 листа</div>
              </div>
              <button className="icon-btn" onClick={() => setSettingsOpen(true)}>
                <Icons.Edit size={13} />
              </button>
            </div>
          </div>

          <div className="rail-cta">
            <button
              className={`cta-create ${processing ? 'processing' : ''}`}
              onClick={runProcess}
              disabled={files.length === 0 || processing}
            >
              {processing ? (
                <>
                  <RotatingSpinner /> Обработка…
                </>
              ) : (
                <>
                  <Icons.Sparkles size={16} sw={2} /> Создать ИУЛ
                </>
              )}
            </button>
            <div className="rail-cta-hint">
              {files.length === 0
                ? 'добавьте файлы, чтобы начать'
                : processing
                  ? 'не закрывайте окно'
                  : <><span className="kbd">⌘</span> <span className="kbd">↵</span> &nbsp; чтобы запустить</>}
            </div>
          </div>
        </aside>
      </div>

      {/* Modal */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        initialTab={settingsTab}
      />

      {/* Toasts */}
      <ToastContainer toasts={toasts} onClose={closeToast} />

      {/* Tweaks */}
      <TweaksPanel title="Tweaks" defaultPosition={{ right: 24, bottom: 24 }}>
        <TweakSection title="Тема">
          <TweakRadio
            label="Theme"
            value={tweaks.theme}
            onChange={(v) => setTweak('theme', v)}
            options={[
              { value: 'dark', label: 'Dark' },
              { value: 'light', label: 'Light' },
            ]}
          />
        </TweakSection>
        <TweakSection title="Акцентный цвет">
          <TweakColor
            label="Accent"
            value={tweaks.accent}
            onChange={(v) => setTweak('accent', v)}
            options={['#3b82f6', '#22c55e', '#f97316', '#a855f7', '#eab308']}
          />
        </TweakSection>
        <TweakSection title="Состояние экрана">
          <TweakRadio
            label="Scenario"
            value={tweaks.scenario}
            onChange={(v) => setTweak('scenario', v)}
            options={[
              { value: 'empty', label: 'Пусто' },
              { value: 'loaded', label: 'Загружено' },
            ]}
          />
          <TweakRadio
            label=" "
            value={tweaks.scenario}
            onChange={(v) => setTweak('scenario', v)}
            options={[
              { value: 'processing', label: 'Идёт' },
              { value: 'done', label: 'Готово' },
            ]}
          />
        </TweakSection>
        <TweakSection title="Окно настроек">
          <button className="btn" onClick={() => { setSettingsTab('project'); setSettingsOpen(true); }} style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Icons.Box size={13} /> Проект
          </button>
          <div style={{ height: 4 }}></div>
          <button className="btn" onClick={() => { setSettingsTab('persons'); setSettingsOpen(true); }} style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Icons.Users size={13} /> Ответственные лица
          </button>
          <div style={{ height: 4 }}></div>
          <button className="btn" onClick={() => { setSettingsTab('signatures'); setSettingsOpen(true); }} style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Icons.PenTool size={13} /> Подписи
          </button>
          <div style={{ height: 4 }}></div>
          <button className="btn" onClick={() => { setSettingsTab('template'); setSettingsOpen(true); }} style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Icons.FileSpreadsheet size={13} /> Шаблон
          </button>
          <div style={{ height: 4 }}></div>
          <button className="btn" onClick={() => { setSettingsTab('system'); setSettingsOpen(true); }} style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Icons.Cpu size={13} /> Система
          </button>
        </TweakSection>
        <TweakSection title="Действия">
          <button
            className="btn"
            onClick={runProcess}
            disabled={processing || files.length === 0}
            style={{ width: '100%' }}
          >
            <Icons.Play size={12} /> Запустить обработку
          </button>
          <div style={{ height: 6 }}></div>
          <button
            className="btn"
            onClick={() => pushToast({ kind: 'info', title: 'Тест уведомления', msg: 'Toast в 14:02' })}
            style={{ width: '100%' }}
          >
            <Icons.Bell size={12} /> Показать toast
          </button>
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

function RotatingSpinner() {
  return (
    <span style={{ display: 'inline-flex', animation: 'spin 0.9s linear infinite' }}>
      <Icons.Loader size={15} sw={2} />
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </span>
  );
}

function nowStr() {
  const d = new Date();
  return d.toTimeString().slice(0, 8);
}

window.IULApp = App;
