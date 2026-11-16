'use client';

import { useEffect, useRef } from 'react';
import { TYPE_LABEL, type Block } from '@/lib/demoDocument';
import { useAccessibility } from '@/lib/accessibility';
import type { Reader } from '@/lib/useReader';
import { useViewerShortcuts } from '@/lib/useShortcuts';
import { Highlighted } from '@/components/Highlighted';

type Props = {
  blocks: Block[];
  reader: Reader;
  onAsk?: () => void;
  onDescribe?: () => void;
};

function FigureCrop({ block }: { block: Block }) {
  const c = block.crop;
  if (!c) return null;
  const px = c.pw === c.w ? 0 : (c.x / (c.pw - c.w)) * 100;
  const py = c.ph === c.h ? 0 : (c.y / (c.ph - c.h)) * 100;
  return (
    <div
      role="img"
      aria-label={block.description ?? 'Hình trong tài liệu, chưa có mô tả'}
      className="w-full max-w-[560px] border-[3px] border-fg bg-white bg-no-repeat"
      style={{
        aspectRatio: `${c.w} / ${c.h}`,
        backgroundImage: `url(${c.url})`,
        backgroundSize: `${(c.pw / c.w) * 100}% ${(c.ph / c.h) * 100}%`,
        backgroundPosition: `${px}% ${py}%`,
      }}
    />
  );
}

function BarChart({ block }: { block: Block }) {
  const data = block.chart ?? [];
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <svg
      role="img"
      aria-label={block.description}
      viewBox="0 0 360 200"
      className="h-auto w-full max-w-[420px]"
    >
      <line x1="20" y1="170" x2="350" y2="170" stroke="var(--fg)" strokeWidth="3" />
      {data.map((d, i) => {
        const h = (d.value / max) * 140;
        const x = 50 + i * 100;
        return (
          <g key={d.label}>
            <rect x={x} y={170 - h} width="60" height={h} fill="var(--ac)" stroke="var(--fg)" strokeWidth="2" />
            <text x={x + 30} y={170 - h - 8} textAnchor="middle" fontSize="16" fontWeight="700" fill="var(--fg)">
              {d.value}
            </text>
            <text x={x + 30} y="192" textAnchor="middle" fontSize="15" fontWeight="700" fill="var(--fg)">
              {d.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function BlockBody({ block, active, reader }: { block: Block; active: boolean; reader: Reader }) {
  const highlighted = (
    <Highlighted
      text={block.text}
      speech={block.speech}
      active={active && reader.playing}
      sentence={reader.sentence}
      wordRange={reader.wordRange}
    />
  );

  if (block.type === 'heading') {
    const Tag = block.level === 1 ? 'h2' : 'h3';
    return (
      <Tag className="font-extrabold text-ac" style={{ fontSize: block.level === 1 ? '1.6em' : '1.35em', lineHeight: 1.3 }}>
        {highlighted}
      </Tag>
    );
  }
  if (block.type === 'figure') {
    return (
      <figure>
        {block.chart ? <BarChart block={block} /> : <FigureCrop block={block} />}
        <figcaption className="mt-2 font-bold">{block.text}</figcaption>
        <p className="mt-1 font-bold text-ac">
          {block.aiDescription && block.description
            ? `Mô tả do AI tạo, có thể chưa chính xác: ${block.description}`
            : 'Chưa có mô tả thay thế. Nhấn D để nghe mô tả.'}
        </p>
      </figure>
    );
  }
  if (block.type === 'table' && block.rows) {
    const [head, ...body] = block.rows;
    return (
      <table className="w-full border-collapse text-left">
        <caption className="mb-2 text-left font-bold">{block.text}</caption>
        <thead>
          <tr>
            {head.map((cell, c) => (
              <th key={c} scope="col" className="border-[3px] border-fg bg-pane px-3 py-2">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, r) => (
            <tr key={r}>
              {row.map((cell, c) =>
                c === 0 ? (
                  <th key={c} scope="row" className="border-[3px] border-fg px-3 py-2">
                    {cell}
                  </th>
                ) : (
                  <td key={c} className="border-[3px] border-fg px-3 py-2">
                    {cell}
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  return <p>{highlighted}</p>;
}

export function DocumentViewer({ blocks, reader, onAsk, onDescribe }: Props) {
  const { zoom, zoomMode } = useAccessibility();
  const onKeyDown = useViewerShortcuts(reader, { onAsk, onDescribe });
  const mounted = useRef(false);

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      return;
    }
    const el = document.getElementById(`block-${reader.current}`);
    if (!el) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' });
  }, [reader.current]);

  return (
    <section
      id="viewer"
      role="application"
      aria-label="Vùng đọc tài liệu. Nhấn F1 để xem bảng phím tắt."
      tabIndex={0}
      onKeyDown={onKeyDown}
      className="rounded-lg border-[3px] border-dashed border-fg p-4"
      style={{
        fontSize: zoomMode === 'reflow' ? `${zoom}%` : undefined,
        paddingBottom: zoomMode === 'lens' ? '45vh' : undefined,
      }}
    >
      <div className="mx-auto flex max-w-[80ch] flex-col gap-4">
        {blocks.map((block, i) => {
          const active = i === reader.current;
          return (
            <div
              key={block.id}
              id={`block-${i}`}
              data-current={active ? 'true' : undefined}
              aria-current={active ? 'true' : undefined}
              onClick={() => reader.goTo(i)}
              className={`relative scroll-my-24 rounded-md border-[6px] p-4 text-left ${
                active ? 'border-ac shadow-[0_0_0_2px_var(--ring-inner)]' : 'border-transparent'
              }`}
            >
              {active && (
                <span className="absolute -top-4 right-3 rounded bg-ac px-2 py-0.5 text-sm font-bold text-onac">
                  Đang đọc {i + 1}/{blocks.length}
                </span>
              )}
              <span className="sr-only">
                {TYPE_LABEL[block.type]} {i + 1} trên {blocks.length}.
              </span>
              <BlockBody block={block} active={active} reader={reader} />
              {block.type !== 'figure' && block.confidence !== undefined && block.confidence < 0.85 && (
                <p className="mt-3 border-2 border-dashed border-fg p-2 text-sm font-bold">
                  ⚠ {block.confidence < 0.6 ? 'Nhận dạng không đủ tin cậy' : 'Nhận dạng chưa chắc chắn'} (
                  {Math.round(block.confidence * 100)}%). Nhấn Q để hỏi AI kiểm tra lại.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
