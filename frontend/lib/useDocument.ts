'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAccessibility } from '@/lib/accessibility';
import { ApiError, getDocument, toBlocks, uploadDocument } from '@/lib/api';
import { DEMO_BLOCKS, type Block } from '@/lib/demoDocument';
import { useEarcons } from '@/lib/useEarcons';

export type DocPhase = 'demo' | 'uploading' | 'processing' | 'ready' | 'error';

export type DocState = {
  phase: DocPhase;
  blocks: Block[];
  version: number;
  docId?: string;
  filename?: string;
  progress: number;
  warnings: string[];
  error?: string;
};

const POLL_MS = 1000;
const MAX_WAIT_MS = 5 * 60 * 1000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useDocument() {
  const { announce } = useAccessibility();
  const { play, startProcessing, stopProcessing } = useEarcons();
  const [state, setState] = useState<DocState>({
    phase: 'demo',
    blocks: DEMO_BLOCKS,
    version: 0,
    progress: 0,
    warnings: [],
  });
  const runRef = useRef(0);

  useEffect(() => {
    return () => {
      runRef.current += 1;
      stopProcessing();
    };
  }, [stopProcessing]);

  const upload = useCallback(
    async (file: File) => {
      const run = ++runRef.current;
      setState((s) => ({ ...s, phase: 'uploading', filename: file.name, progress: 0, error: undefined, warnings: [] }));
      announce(`Đang tải lên ${file.name}`);
      startProcessing();
      try {
        let job = await uploadDocument(file);
        if (run !== runRef.current) return;
        setState((s) => ({ ...s, phase: 'processing', docId: job.id }));
        announce('Đang phân tích bố cục và nhận dạng chữ');
        const started = Date.now();
        while (job.status === 'queued' || job.status === 'processing') {
          if (Date.now() - started > MAX_WAIT_MS) throw new ApiError('Xử lý quá lâu, vui lòng thử tài liệu nhỏ hơn');
          await sleep(POLL_MS);
          if (run !== runRef.current) return;
          job = await getDocument(job.id);
          if (run !== runRef.current) return;
          const progress = job.progress;
          setState((s) => ({ ...s, progress }));
        }
        if (job.status === 'error' || !job.result) throw new ApiError(job.error ?? 'Xử lý tài liệu thất bại');
        const blocks = toBlocks(job.result);
        if (!blocks.length) throw new ApiError('Không tìm thấy nội dung nào trong tài liệu này');
        const warnings = job.result.warnings;
        const docId = job.id;
        stopProcessing();
        setState((s) => ({
          phase: 'ready',
          blocks,
          version: s.version + 1,
          docId,
          filename: file.name,
          progress: 1,
          warnings,
        }));
        announce(`Đã xử lý xong ${file.name}, có ${blocks.length} mục`);
        play('done');
      } catch (error) {
        if (run !== runRef.current) return;
        stopProcessing();
        const message = error instanceof Error ? error.message : 'Có lỗi không xác định';
        setState((s) => ({ ...s, phase: 'error', error: message }));
        announce(message);
        play('error');
      }
    },
    [announce, play, startProcessing, stopProcessing],
  );

  const useDemo = useCallback(() => {
    runRef.current += 1;
    stopProcessing();
    setState((s) => ({
      phase: 'demo',
      blocks: DEMO_BLOCKS,
      version: s.version + 1,
      progress: 0,
      warnings: [],
    }));
    announce('Đã chuyển về tài liệu mẫu');
  }, [announce, stopProcessing]);

  return { state, upload, useDemo };
}

export type DocumentController = ReturnType<typeof useDocument>;
