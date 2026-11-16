'use client';

import { useRef } from 'react';
import { API_BASE } from '@/lib/api';
import type { DocumentController } from '@/lib/useDocument';

const PHASE_TEXT = {
  demo: 'Đang dùng tài liệu mẫu',
  uploading: 'Đang tải lên',
  processing: 'Đang phân tích bố cục và nhận dạng chữ',
  ready: 'Đã xử lý xong',
  error: 'Có lỗi',
} as const;

export function UploadBar({ doc }: { doc: DocumentController }) {
  const { state, upload, useDemo } = doc;
  const inputRef = useRef<HTMLInputElement>(null);
  const busy = state.phase === 'uploading' || state.phase === 'processing';
  const percent = Math.round(state.progress * 100);

  return (
    <section
      aria-label="Tài liệu"
      className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-4 gap-y-2 border-b-[3px] border-fg px-4 py-3"
    >
      <input
        ref={inputRef}
        type="file"
        hidden
        accept=".pdf,application/pdf,image/png,image/jpeg,image/webp"
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = '';
          if (file) void upload(file);
        }}
      />
      <button type="button" className="btn btn-primary" disabled={busy} onClick={() => inputRef.current?.click()}>
        Tải tài liệu lên (PDF, PNG, JPG)
      </button>
      <button type="button" className="btn" disabled={busy || state.phase === 'demo'} onClick={useDemo}>
        Dùng tài liệu mẫu
      </button>
      <p className="font-bold">
        {state.filename && state.phase !== 'demo' ? `${state.filename}: ` : ''}
        {PHASE_TEXT[state.phase]}
        {busy && state.phase === 'processing' ? ` (${percent}%)` : ''}
        {state.phase === 'ready' ? `, ${state.blocks.length} mục` : ''}
      </p>
      {busy && <progress className="h-3 w-40" max={100} value={percent} aria-label="Tiến độ xử lý" />}
      {state.phase === 'error' && state.error && (
        <p className="w-full rounded-md border-[3px] border-dashed border-fg p-2 font-bold text-ac" role="alert">
          Lỗi: {state.error}
        </p>
      )}
      {state.phase === 'ready' && state.warnings.length > 0 && (
        <p className="w-full font-bold">Lưu ý: {state.warnings.join('; ')}</p>
      )}
      <p className="ml-auto text-sm font-bold" aria-hidden="true">
        Máy chủ: {API_BASE}
      </p>
    </section>
  );
}
