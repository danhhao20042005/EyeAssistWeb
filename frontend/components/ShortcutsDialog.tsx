'use client';

import { Fragment, useEffect, useRef } from 'react';
import { useAccessibility } from '@/lib/accessibility';
import { SHORTCUT_GROUPS } from '@/lib/shortcuts';

export function ShortcutsDialog() {
  const { helpOpen, closeHelp, shortcutsEnabled, toggleShortcuts } = useAccessibility();
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (helpOpen && !dialog.open) dialog.showModal();
    if (!helpOpen && dialog.open) dialog.close();
  }, [helpOpen]);

  return (
    <dialog
      ref={ref}
      aria-labelledby="shortcuts-title"
      onClose={closeHelp}
      onClick={(event) => {
        if (event.target === ref.current) closeHelp();
      }}
      className="max-h-[92vh] w-[94vw] max-w-5xl overflow-auto rounded-xl border-[6px] border-ac bg-bg p-6 text-fg backdrop:bg-black/70"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="shortcuts-title" className="text-2xl font-extrabold text-ac">
            Bảng phím tắt điều hướng
          </h2>
          <p className="mt-1 font-bold">
            Mở bằng F1 hoặc ?. Đóng bằng Esc. Phím đơn chỉ hoạt động khi vùng đọc tài liệu đang có focus.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={closeHelp}>
          Đóng (Esc)
        </button>
      </div>

      <div className="mt-5 grid gap-6 md:grid-cols-2">
        {SHORTCUT_GROUPS.map((group) => (
          <section key={group.group} aria-labelledby={`sg-${group.group}`}>
            <h3 id={`sg-${group.group}`} className="mb-2 border-b-[3px] border-ac pb-1 text-lg font-extrabold text-ac">
              {group.group}
            </h3>
            <ul className="flex flex-col gap-2">
              {group.items.map((item) => (
                <li key={item.label} className="flex flex-wrap items-center gap-2">
                  <span className="flex items-center gap-1">
                    {item.keys.map((k, i) => (
                      <Fragment key={k}>
                        {i > 0 && <span className="font-bold">hoặc</span>}
                        <kbd className="kbd">{k}</kbd>
                      </Fragment>
                    ))}
                  </span>
                  <span className="font-bold">
                    {item.label}
                    {item.pending ? ' (sắp có)' : ''}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 border-t-[3px] border-fg pt-4">
        <button type="button" className="btn" aria-pressed={shortcutsEnabled} onClick={toggleShortcuts}>
          Phím đơn: {shortcutsEnabled ? 'Bật' : 'Tắt'}
        </button>
        <p className="font-bold">Tắt phím đơn nếu bạn dùng screen reader hoặc gõ nhầm phím (WCAG 2.1.4). Mũi tên vẫn dùng được.</p>
      </div>
    </dialog>
  );
}
