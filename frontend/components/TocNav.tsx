'use client';

import type { Block } from '@/lib/demoDocument';
import type { Reader } from '@/lib/useReader';

export function TocNav({ blocks, reader }: { blocks: Block[]; reader: Reader }) {
  const headings = blocks
    .map((block, index) => ({ block, index }))
    .filter(({ block }) => block.type === 'heading');

  const jump = (index: number) => {
    reader.goTo(index);
    document.getElementById('viewer')?.focus();
  };

  return (
    <nav aria-label="Mục lục" className="rounded-lg border-[3px] border-fg bg-pane p-3">
      <h2 className="mb-2 text-base font-extrabold text-ac">MỤC LỤC</h2>
      <ul className="flex flex-col gap-2">
        {headings.map(({ block, index }) => {
          const active = reader.current === index;
          return (
            <li key={block.id}>
              <button
                type="button"
                className={`btn w-full justify-start text-left ${block.level === 1 ? '' : 'pl-5'}`}
                aria-current={active ? 'location' : undefined}
                aria-pressed={active}
                onClick={() => jump(index)}
              >
                {block.text}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
