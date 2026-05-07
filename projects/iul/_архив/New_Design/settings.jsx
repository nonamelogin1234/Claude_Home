/* global React, Icons, IUL_DATA */
// Settings modal — 5 sections, fully tabbed.

const { useState: uS } = React;

function SettingsModal({ open, onClose, initialTab }) {
  const [tab, setTab] = uS(initialTab || 'project');
  const [persons, setPersons] = uS(IUL_DATA.PERSONS);

  if (!open) return null;

  const tabs = [
    { id: 'project', label: 'Проект', icon: <Icons.Box size={15} /> },
    { id: 'persons', label: 'Ответственные лица', icon: <Icons.Users size={15} /> },
    { id: 'signatures', label: 'Подписи', icon: <Icons.PenTool size={15} /> },
    { id: 'template', label: 'Шаблон', icon: <Icons.FileSpreadsheet size={15} /> },
    { id: 'system', label: 'Система', icon: <Icons.Cpu size={15} /> },
  ];

  const headerMap = {
    project: { h: 'Проект', s: 'Шифр и правила парсинга имён файлов' },
    persons: { h: 'Ответственные лица', s: 'ФИО исполнителей по разделам проекта' },
    signatures: { h: 'Подписи', s: 'PNG-подписи и автосопоставление с ФИО' },
    template: { h: 'Шаблон Excel', s: 'Заменить или восстановить шаблон ИУЛ' },
    system: { h: 'Система', s: 'Хранилище, диагностика, экспорт логов' },
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <aside className="modal-side">
          <div className="modal-side-title">Настройки</div>
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`modal-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </aside>
        <div className="modal-main">
          <div className="modal-header">
            <div>
              <div className="modal-h">{headerMap[tab].h}</div>
              <div className="modal-h-sub">{headerMap[tab].s}</div>
            </div>
            <button className="icon-btn" onClick={onClose}><Icons.X size={16} /></button>
          </div>
          <div className="modal-content scroll-area">
            {tab === 'project' && <TabProject />}
            {tab === 'persons' && <TabPersons persons={persons} setPersons={setPersons} />}
            {tab === 'signatures' && <TabSignatures />}
            {tab === 'template' && <TabTemplate />}
            {tab === 'system' && <TabSystem />}
          </div>
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={onClose}>Отмена</button>
            <button className="btn btn-primary" onClick={onClose}>
              <Icons.Check size={14} sw={2.5} /> Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function TabProject() {
  return (
    <>
      <div className="field">
        <label className="field-label">Шифр проекта</label>
        <input className="input mono" defaultValue="1605-2022" />
        <div className="field-hint">Подставляется в ИУЛ как идентификатор объекта.</div>
      </div>
      <div className="field">
        <label className="field-label">Шаблон именования файлов</label>
        <input
          className="input mono"
          defaultValue="Раздел ПД №{N} [подраздел ПД №{N}] {ШифрРаздела} [часть №{N}] [книга №{N}].pdf"
        />
        <div className="field-hint">
          Поддерживаются шифры: <span style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>АР · КР · ПЗУ · ИОС1–ИОС7</span>
        </div>
      </div>
      <div className="field">
        <label className="field-label">Папка результата по умолчанию</label>
        <div style={{ display: 'flex', gap: 6 }}>
          <input className="input mono" defaultValue="C:\Users\gor-r\Documents\ИУЛ\out" style={{ flex: 1 }} />
          <button className="btn"><Icons.FolderOpen size={14} /> Обзор</button>
        </div>
      </div>
      <div className="field" style={{ marginBottom: 0 }}>
        <label className="field-label">Авто-нумерация изменения</label>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input className="input mono" defaultValue="1" style={{ width: 90 }} />
          <span style={{ fontSize: 12.5, color: 'var(--text-mute)' }}>
            Будет увеличиваться автоматически при следующей выгрузке.
          </span>
        </div>
      </div>
    </>
  );
}

function TabPersons({ persons, setPersons }) {
  const update = (idx, key, val) => {
    const next = [...persons];
    next[idx] = { ...next[idx], [key]: val };
    setPersons(next);
  };
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div className="field-hint" style={{ margin: 0 }}>
          Подставляются в ИУЛ как ФИО исполнителей по каждому разделу.
        </div>
        <button className="btn"><Icons.Plus size={14} /> Добавить роль</button>
      </div>
      <table className="persons-table">
        <thead>
          <tr>
            <th>Роль</th>
            <th>АР</th>
            <th>КР</th>
            <th>ПЗУ</th>
            <th>ИОС</th>
          </tr>
        </thead>
        <tbody>
          {persons.map((p, i) => (
            <tr key={i}>
              <td>{p.role}</td>
              <td><input className="input" value={p.AR} onChange={(e) => update(i, 'AR', e.target.value)} /></td>
              <td><input className="input" value={p.KR} onChange={(e) => update(i, 'KR', e.target.value)} /></td>
              <td><input className="input" value={p.PZU} onChange={(e) => update(i, 'PZU', e.target.value)} /></td>
              <td><input className="input" value={p.IOS} onChange={(e) => update(i, 'IOS', e.target.value)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function SignatureSvg() {
  // simple stylized squiggle, varies by index
  return (
    <svg viewBox="0 0 100 40">
      <path d="M5 28 C 12 8, 22 8, 30 22 S 50 36, 60 18 S 80 8, 95 24"
        fill="none" stroke="var(--text)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function TabSignatures() {
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div className="field-hint" style={{ margin: 0 }}>
          Перетащите PNG в карточку, чтобы заменить. Совпадения по ФИО ищутся автоматически.
        </div>
        <button className="btn btn-primary"><Icons.Plus size={14} sw={2.5} /> Добавить подпись</button>
      </div>
      <div className="sig-grid">
        {IUL_DATA.SIGNATURES.map((s) => (
          <div key={s.id} className="sig-card">
            <div className="sig-preview"><SignatureSvg /></div>
            <div className="sig-info">
              <div className="sig-name">{s.name}</div>
              <div className="sig-role">{s.role}</div>
              <div style={{ marginTop: 6, display: 'flex', gap: 4, alignItems: 'center' }}>
                {s.detected ? (
                  <span className="status status-done" style={{ height: 18 }}>
                    <span className="status-dot"></span>сопоставлено
                  </span>
                ) : (
                  <span className="status status-warning" style={{ height: 18 }}>
                    <span className="status-dot"></span>не найдено
                  </span>
                )}
              </div>
            </div>
            <div className="sig-actions">
              <button className="icon-btn" title="Заменить"><Icons.RefreshCw size={14} /></button>
              <button className="icon-btn" title="Удалить"><Icons.Trash size={14} /></button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function TabTemplate() {
  return (
    <>
      <div className="template-card">
        <div className="template-icon"><span>XLSX</span></div>
        <div className="template-info">
          <div style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--text-strong)' }}>ИУЛ_шаблон.xlsx</div>
          <div className="template-path">C:\Users\gor-r\AppData\Roaming\ИУЛ\ИУЛ_шаблон.xlsx</div>
          <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 11.5, color: 'var(--text-faint)', fontFamily: 'var(--mono)' }}>
            <span>1.2 МБ</span><span>·</span><span>4 листа</span><span>·</span><span>обновлён 2026-04-12</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn"><Icons.Eye size={14} /> Открыть</button>
          <button className="btn"><Icons.RefreshCw size={14} /> Заменить</button>
        </div>
      </div>
      <div style={{ marginTop: 16, padding: 14, border: '1px solid var(--border)', borderRadius: 10, background: 'var(--bg-elev-2)' }}>
        <div style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--text-strong)', marginBottom: 4 }}>Восстановить шаблон по умолчанию</div>
        <div style={{ fontSize: 12, color: 'var(--text-mute)', marginBottom: 10 }}>
          Заменит текущий шаблон встроенным в приложение. Текущий будет сохранён в резервной копии.
        </div>
        <button className="btn"><Icons.Download size={14} /> Восстановить дефолтный</button>
      </div>
    </>
  );
}

function TabSystem() {
  return (
    <>
      <div className="diag-row">
        <div className="diag-info">
          <div className="diag-icon"><Icons.HardDrive size={16} /></div>
          <div>
            <div className="diag-name">Каталог пользовательских данных</div>
            <div className="diag-meta">C:\Users\gor-r\AppData\Roaming\ИУЛ · 84 МБ</div>
          </div>
        </div>
        <button className="btn"><Icons.FolderOpen size={14} /> Открыть</button>
      </div>
      <div className="diag-row">
        <div className="diag-info">
          <div className="diag-icon"><Icons.FileSpreadsheet size={16} /></div>
          <div>
            <div className="diag-name">Excel COM</div>
            <div className="diag-meta">Microsoft Excel 16.0 · подключён</div>
          </div>
        </div>
        <span className="status status-done"><span className="status-dot"></span>OK</span>
      </div>
      <div className="diag-row">
        <div className="diag-info">
          <div className="diag-icon"><Icons.Trash size={16} /></div>
          <div>
            <div className="diag-name">Временные файлы</div>
            <div className="diag-meta">128 файлов · 12 МБ</div>
          </div>
        </div>
        <button className="btn">Очистить</button>
      </div>
      <div className="diag-row">
        <div className="diag-info">
          <div className="diag-icon"><Icons.Activity size={16} /></div>
          <div>
            <div className="diag-name">Экспорт логов</div>
            <div className="diag-meta">.txt-архив за последние 30 дней</div>
          </div>
        </div>
        <button className="btn"><Icons.Download size={14} /> Экспортировать</button>
      </div>
      <div className="diag-row">
        <div className="diag-info">
          <div className="diag-icon"><Icons.Cpu size={16} /></div>
          <div>
            <div className="diag-name">Диагностика</div>
            <div className="diag-meta">Запустить полную проверку Excel COM и шаблона</div>
          </div>
        </div>
        <button className="btn"><Icons.Zap size={14} /> Запустить</button>
      </div>
      <div style={{ marginTop: 18, fontSize: 11, color: 'var(--text-faint)', fontFamily: 'var(--mono)', textAlign: 'center' }}>
        ИУЛ · v3.2.0 · build 2026.04
      </div>
    </>
  );
}

window.SettingsModal = SettingsModal;
