'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { askVqa } from '@/lib/api';
import type { Block } from '@/lib/demoDocument';
import { useAccessibility } from '@/lib/accessibility';
import { useReader } from '@/lib/useReader';
import { useEarcons } from '@/lib/useEarcons';
import type { EarconName } from '@/lib/earcons';
import { warningEarcon } from '@/lib/earconSync';
import { CONFIDENT_THRESHOLD, LOW_THRESHOLD } from '@/lib/thresholds';
import { useDocument } from '@/lib/useDocument';
import { useGlobalShortcuts } from '@/lib/useShortcuts';
import { Toolbar } from '@/components/Toolbar';
import { UploadBar } from '@/components/UploadBar';
import { TocNav } from '@/components/TocNav';
import { DocumentViewer } from '@/components/DocumentViewer';
import { ZoomPanel } from '@/components/ZoomPanel';
import { PlayerBar } from '@/components/PlayerBar';
import { ShortcutsDialog } from '@/components/ShortcutsDialog';
import { AskDialog, LEVEL_EARCON } from '@/components/AskDialog';

const DESCRIBE_QUESTION = 'Mô tả chi tiết hình hoặc biểu đồ này cho người khiếm thị, nêu rõ các số liệu nhìn thấy được.';

type WorkspaceProps = {
  baseBlocks: Block[];
  docId?: string;
};

function Workspace({ baseBlocks, docId }: WorkspaceProps) {
  const { announce, follow, zoomMode } = useAccessibility();
  const { play, playSequence, cancel: stopEarcons } = useEarcons();
  const [descriptions, setDescriptions] = useState<Record<string, string>>({});
  const [askOpen, setAskOpen] = useState(false);

  const blocks = useMemo(
    () =>
      baseBlocks.map((block) =>
        descriptions[block.id] ? { ...block, description: descriptions[block.id], aiDescription: true } : block,
      ),
    [baseBlocks, descriptions],
  );

  // Âm loại khối, rồi (nếu OCR không chắc) âm cảnh báo nối ngay sau đó. Trả về tổng thời lượng để giọng đọc chờ xong.
  const onNavigate = useCallback(
    (block: Block): number => {
      const names: EarconName[] = [block.type];
      const warning = block.type === 'figure' ? null : warningEarcon(block.confidence, CONFIDENT_THRESHOLD, LOW_THRESHOLD);
      if (warning) names.push(warning);
      return playSequence(names);
    },
    [playSequence],
  );

  const reader = useReader({ blocks, announce, onNavigate, stopEarcons });
  const [pinned, setPinned] = useState(0);

  useEffect(() => {
    if (follow) setPinned(reader.current);
  }, [follow, reader.current]);

  const openAsk = useCallback(() => setAskOpen(true), []);
  const closeAsk = useCallback(() => {
    setAskOpen(false);
    document.getElementById('viewer')?.focus();
  }, []);

  const describe = useCallback(async () => {
    const block = blocks[reader.current];
    if (block.type !== 'figure') {
      announce('Mục này không phải hình hoặc biểu đồ');
      return;
    }
    if (block.description) {
      reader.describeFigure();
      return;
    }
    if (!docId) {
      announce('Hình này chưa có mô tả');
      return;
    }
    announce('Đang nhờ AI mô tả hình, vui lòng chờ');
    try {
      const answer = await askVqa({ question: DESCRIBE_QUESTION, documentId: docId, blockId: block.id });
      setDescriptions((prev) => ({ ...prev, [block.id]: answer.answer }));
      const earconMs = play(LEVEL_EARCON[answer.uncertainty_level]);
      const prefix = answer.uncertainty_level === 'confident' ? '' : 'AI chưa chắc chắn về mô tả này. ';
      reader.speakText(`${prefix}${answer.answer}`, earconMs); // chờ âm báo xong rồi mới đọc
    } catch (error) {
      announce(error instanceof Error ? error.message : 'Không mô tả được hình');
      play('error');
    }
  }, [announce, blocks, docId, play, reader]);

  const panelIndex = follow ? reader.current : pinned;
  const panel = (
    <ZoomPanel
      block={blocks[panelIndex] ?? blocks[0]}
      index={panelIndex}
      total={blocks.length}
      isCurrent={panelIndex === reader.current}
      sentence={reader.sentence}
      wordRange={reader.wordRange}
    />
  );

  const docked = zoomMode === 'docked';
  const lens = zoomMode === 'lens';

  return (
    <>
      <div
        className={`mx-auto grid max-w-[1600px] gap-4 px-4 py-4 ${
          docked
            ? 'lg:grid-cols-[240px_minmax(0,1fr)_minmax(340px,42%)]'
            : 'lg:grid-cols-[240px_minmax(0,1fr)]'
        }`}
      >
        <TocNav blocks={blocks} reader={reader} />
        <main>
          <DocumentViewer blocks={blocks} reader={reader} onAsk={openAsk} onDescribe={describe} />
        </main>
        {docked && <div>{panel}</div>}
      </div>
      {lens && panel}
      <PlayerBar reader={reader} total={blocks.length} onAsk={openAsk} />
      <AskDialog
        open={askOpen}
        onClose={closeAsk}
        block={blocks[reader.current]}
        index={reader.current}
        total={blocks.length}
        docId={docId}
        speak={reader.speakText}
      />
    </>
  );
}

export function EyeAssistApp() {
  const doc = useDocument();
  useGlobalShortcuts();

  return (
    <>
      <a href="#viewer" className="btn btn-primary sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50">
        Bỏ qua tới vùng đọc
      </a>
      <Toolbar />
      <UploadBar doc={doc} />
      <Workspace key={doc.state.version} baseBlocks={doc.state.blocks} docId={doc.state.docId} />
      <ShortcutsDialog />
    </>
  );
}
