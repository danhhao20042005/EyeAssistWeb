'use client';

import { TYPE_LABEL, type Block } from '@/lib/demoDocument';
import { useAccessibility } from '@/lib/accessibility';
import type { WordRange } from '@/lib/useReader';
import { Highlighted, currentWord } from '@/components/Highlighted';

type Props = {
  block: Block;
  index: number;
  total: number;
  isCurrent: boolean;
  sentence: number;
  wordRange: WordRange;
};

export function ZoomPanel({ block, index, total, isCurrent, sentence, wordRange }: Props) {
  const { zoom, zoomMode, follow } = useAccessibility();
  const word = isCurrent ? currentWord(block.text, block.speech, sentence, wordRange) : null;

  const wrapper =
    zoomMode === 'lens'
      ? 'fixed inset-x-4 bottom-24 z-20 max-h-[40vh] overflow-auto'
      : 'lg:sticky lg:top-4 lg:max-h-[calc(100vh-9rem)] overflow-auto';

  return (
    <aside
      aria-label={`Vùng zoom động ${zoom} phần trăm`}
      className={`${wrapper} rounded-lg border-[6px] border-ac bg-bg p-4 text-fg`}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-extrabold text-ac">
          Vùng zoom {zoom}% {follow ? '- bám theo vùng đọc' : '- đã ghim'}
        </h2>
        <span className="rounded bg-ac px-2 py-1 text-sm font-bold text-onac">
          {TYPE_LABEL[block.type]} {index + 1}/{total}
        </span>
      </div>

      <div aria-hidden="true" style={{ fontSize: `${zoom / 100}rem`, lineHeight: 1.5 }} className="font-bold">
        {block.type === 'table' && block.rows ? (
          <table className="w-full border-collapse">
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => (
                    <td key={c} className="border-2 border-fg px-2 py-1">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : block.type === 'figure' ? (
          <p>{block.description ?? block.text}</p>
        ) : (
          <p>
            <Highlighted
              text={block.text}
              speech={block.speech}
              active={isCurrent}
              sentence={sentence}
              wordRange={wordRange}
            />
          </p>
        )}
      </div>

      <p className="mt-3 border-t-2 border-fg pt-2 text-base font-bold" aria-hidden="true">
        Từ đang đọc: {word ?? '-'}
      </p>
    </aside>
  );
}
