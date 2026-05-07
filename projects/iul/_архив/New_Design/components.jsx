/* global React, Icons */
// File row + status pill + drop zone + console + toast components.

const { useState, useEffect, useRef, useCallback } = React;

// === Status pill ===
function StatusPill({ status }) {
  const I = Icons;
  const map = {
    idle: { label: 'В очереди', cls: 'status-idle', icon: <I.Hash size={11} /> },
    parsing: { label: 'Парсинг', cls: 'status-parsing', icon: <I.Search size={11} /> },
    processing: { label: 'Обработка', cls: 'status-processing', icon: <I.Cog size={11} /> },
    exporting: { label: 'Экспорт', cls: 'status-exporting', icon: <I.Download size={11} /> },
    done: { label: 'Готово', cls: 'status-done', icon: <I.Check size={11} /> },
    warning: { label: 'Предупр.', cls: 'status-warning', icon: <I.AlertTriangle size={11} /> },
    error: { label: 'Ошибка', cls: 'status-error', icon: <I.AlertCircle size={11} /> },
  };
  const m = map[status] || map.idle;
  return (
    <span className={`status ${m.cls}`}>
      <span className="status-dot"></span>
      {m.label}
    </span>
  );
}

// === Drop zone ===
function DropZone({ onAddFiles, hasFiles }) {
  const [drag, setDrag] = useState(false);
  const onDragOver = (e) => { e.preventDefault(); setDrag(true); };
  const onDragLeave = (e) => { e.preventDefault(); setDrag(false); };
  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    onAddFiles && onAddFiles();
  };
  if (hasFiles) {
    return (
      <div
        className={`drop-zone compact ${drag ? 'drag-over' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={onAddFiles}
      >
        <div className="drop-zone-icon">
          <Icons.Upload size={18} sw={1.8} />
        </div>
        <div className="drop-zone-meta">
          <div className="drop-zone-title">Перетащите PDF, чтобы добавить в очередь</div>
          <div className="drop-zone-sub">либо выберите вручную · поддерживается множественный выбор</div>
        </div>
        <div className="drop-zone-actions">
          <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); onAddFiles && onAddFiles(); }}>
            <Icons.FilePlus size={14} sw={2} /> Выбрать файлы
          </button>
        </div>
      </div>
    );
  }
  return (
    <div
      className={`drop-zone ${drag ? 'drag-over' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={onAddFiles}
    >
      <div className="drop-zone-icon">
        <Icons.Upload size={26} sw={1.6} />
      </div>
      <div className="drop-zone-title">
        Перетащите PDF-файлы сюда
      </div>
      <div className="drop-zone-sub">
        либо нажмите, чтобы выбрать вручную · поддерживается множественный выбор
      </div>
      <div className="drop-zone-actions">
        <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); onAddFiles && onAddFiles(); }}>
          <Icons.FilePlus size={14} sw={2} /> Выбрать файлы
        </button>
        <button className="btn btn-ghost" onClick={(e) => e.stopPropagation()}>
          <Icons.Folder size={14} /> Открыть папку
        </button>
      </div>
      <div className="drop-zone-hint">
        <Icons.Info size={12} />
        Формат:&nbsp; Раздел ПД №N [подраздел ПД №N] ШифрРаздела [часть №N] [книга №N].pdf
      </div>
    </div>
  );
}

// === File row ===
function FileRow({ file, onRemove }) {
  return (
    <div className="file-row" data-status={file.status}>
      <div className="file-cell-name">
        <div className="file-icon">PDF</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="file-name">{file.name}</div>
          <div className="file-meta">
            <span>{file.size}</span>
            <span className="file-meta-sep">·</span>
            <span>CRC {file.crc}</span>
            <span className="file-meta-sep">·</span>
            <span>{file.date}</span>
            {file.warnings > 0 && (
              <>
                <span className="file-meta-sep">·</span>
                <span style={{ color: 'var(--amber)' }}>
                  {file.warnings} {file.warnings === 1 ? 'предупр.' : 'предупр.'}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
      <div>
        <div className="section-tags">
          <span className={`tag ${file.sectionTone}`}>{file.section}</span>
          <span style={{ color: 'var(--text-faint)', fontSize: 12, alignSelf: 'center' }}>
            {file.sectionLabel.replace(file.section, '').trim().replace(/^·\s*/, '')}
          </span>
        </div>
      </div>
      <div><StatusPill status={file.status} /></div>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button className="icon-btn" onClick={() => onRemove && onRemove(file.id)} title="Удалить из очереди">
          <Icons.X size={14} />
        </button>
      </div>
      {file.progress > 0 && file.progress < 100 && (
        <div className="row-progress" style={{ width: `${file.progress}%` }}></div>
      )}
    </div>
  );
}

// === Console ===
function Console({ logs, open, onToggle }) {
  const [filter, setFilter] = useState('all');
  const bodyRef = useRef(null);

  const filtered = logs.filter((l) => filter === 'all' || l.level === filter || (filter === 'warn' && l.level === 'warn') || (filter === 'error' && l.level === 'error'));

  useEffect(() => {
    if (open && bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [logs, open]);

  const counts = {
    all: logs.length,
    warn: logs.filter((l) => l.level === 'warn').length,
    error: logs.filter((l) => l.level === 'error').length,
  };

  return (
    <div className={`console ${open ? 'open' : ''}`}>
      <div className="console-header" onClick={onToggle}>
        <div className="console-title-row">
          <span className="console-chev"><Icons.ChevronRight size={14} /></span>
          <Icons.Terminal size={13} />
          <span>Журнал обработки</span>
          <span className="console-count">{logs.length}</span>
        </div>
        <div className="console-filters" onClick={(e) => e.stopPropagation()}>
          <button className={`console-filter ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
            Все
          </button>
          <button className={`console-filter ${filter === 'warn' ? 'active' : ''}`} onClick={() => setFilter('warn')}>
            <span className="dot" style={{ background: 'var(--amber)' }}></span>
            Предупр. <span style={{ color: 'var(--text-faint)' }}>{counts.warn}</span>
          </button>
          <button className={`console-filter ${filter === 'error' ? 'active' : ''}`} onClick={() => setFilter('error')}>
            <span className="dot" style={{ background: 'var(--red)' }}></span>
            Ошибки <span style={{ color: 'var(--text-faint)' }}>{counts.error}</span>
          </button>
        </div>
      </div>
      <div className="console-body">
        <div className="console-log scroll-area" ref={bodyRef}>
          {filtered.map((l, i) => (
            <div key={i} className="log-line">
              <span className="log-time">{l.time}</span>
              <span className={`log-level ${l.level}`}>{l.level}</span>
              <span className="log-msg">{l.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// === Toasts ===
function Toast({ toast, onClose }) {
  const I = Icons;
  const iconMap = {
    success: <I.Check size={14} sw={2.5} />,
    error: <I.AlertCircle size={14} />,
    warn: <I.AlertTriangle size={14} />,
    info: <I.Info size={14} />,
  };
  return (
    <div className={`toast ${toast.leaving ? 'leaving' : ''}`}>
      <div className={`toast-icon ${toast.kind}`}>{iconMap[toast.kind]}</div>
      <div className="toast-body">
        <div className="toast-title">{toast.title}</div>
        {toast.msg && <div className="toast-msg">{toast.msg}</div>}
      </div>
      <button className="toast-close" onClick={() => onClose(toast.id)}>
        <I.X size={13} />
      </button>
    </div>
  );
}

function ToastContainer({ toasts, onClose }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => <Toast key={t.id} toast={t} onClose={onClose} />)}
    </div>
  );
}

Object.assign(window, { StatusPill, DropZone, FileRow, Console, Toast, ToastContainer });
