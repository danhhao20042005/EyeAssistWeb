'use client';

import { useEffect, useState } from 'react';
import { DEMO_BLOCKS } from '@/lib/demoDocument';
import { useAccessibility } from '@/lib/accessibility';
import { useReader } from '@/lib/useReader';
import { useGlobalShortcuts } from '@/lib/useShortcuts';
import { Toolbar } from '@/components/Toolbar';
import { TocNav } from '@/components/TocNav';
import { DocumentViewer } from '@/components/DocumentViewer';
import { ZoomPanel } from '@/components/ZoomPanel';
import { PlayerBar } from '@/components/PlayerBar';
import { ShortcutsDialog } from '@/components/ShortcutsDialog';

export function EyeAssistApp() {
  const { announce, follow, zoomMode } = useAccessibility();
  const reader = useReader({ blocks: DEMO_BLOCKS, announce });
  const [pinned, setPinned] = useState(0);

  useGlobalShortcuts();

  useEffect(() => {
    if (follow) setPinned(reader.current);
  }, [follow, reader.current]);

  const panelIndex = follow ? reader.current : pinned;
  const panel = (
    <ZoomPanel
      block={DEMO_BLOCKS[panelIndex]}
      index={panelIndex}
      total={DEMO_BLOCKS.length}
      isCurrent={panelIndex === reader.current}
      sentence={reader.sentence}
      wordRange={reader.wordRange}
    />
  );

  const docked = zoomMode === 'docked';
  const lens = zoomMode === 'lens';

  return (
    <>
      <a href="#viewer" className="btn btn-primary sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50">
        Bỏ qua tới vùng đọc
      </a>
      <Toolbar />
      <div
        className={`mx-auto grid max-w-[1600px] gap-4 px-4 py-4 ${
          docked
            ? 'lg:grid-cols-[240px_minmax(0,1fr)_minmax(340px,42%)]'
            : 'lg:grid-cols-[240px_minmax(0,1fr)]'
        }`}
      >
        <TocNav blocks={DEMO_BLOCKS} reader={reader} />
        <main>
          <DocumentViewer blocks={DEMO_BLOCKS} reader={reader} />
        </main>
        {docked && <div>{panel}</div>}
      </div>
      {lens && panel}
      <PlayerBar reader={reader} total={DEMO_BLOCKS.length} />
      <ShortcutsDialog />
    </>
  );
}
