'use client';

import { useAccessibility } from '@/lib/accessibility';
import type { Reader } from '@/lib/useReader';

export function PlayerBar({ reader, total }: { reader: Reader; total: number }) {
  const { announcement } = useAccessibility();

  return (
    <footer className="sticky bottom-0 z-30 border-t-[3px] border-fg bg-bg">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-3 px-4 py-3">
        <button type="button" className="btn" onClick={reader.prev}>
          ‹ Trước (K)
        </button>
        <button type="button" className="btn btn-primary" onClick={reader.toggle}>
          {reader.playing ? 'Tạm dừng (Space)' : 'Phát (Space)'}
        </button>
        <button type="button" className="btn" onClick={reader.next}>
          Sau (J) ›
        </button>
        <button type="button" className="btn" onClick={reader.stop}>
          Dừng (S)
        </button>
        <span className="font-bold">Tốc độ: {reader.speed.toFixed(2).replace(/0$/, '')}x ([ ])</span>
        <span className="font-bold">
          Mục {reader.current + 1}/{total}
        </span>
        <p role="status" aria-live="polite" className="ml-auto min-w-[12rem] font-bold text-ac">
          {announcement || 'Sẵn sàng'}
        </p>
      </div>
    </footer>
  );
}
