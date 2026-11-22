'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { askVqa, type UncertaintyLevel, type VqaResult } from '@/lib/api';
import { TYPE_LABEL, type Block } from '@/lib/demoDocument';
import { useEarcons } from '@/lib/useEarcons';
import type { EarconName } from '@/lib/earcons';

type Props = {
  open: boolean;
  onClose: () => void;
  block: Block | undefined;
  index: number;
  total: number;
  docId?: string;
  speak: (text: string, earconMs?: number) => void;
};

export const LEVEL_LABEL: Record<UncertaintyLevel, string> = {
  confident: 'Tin cậy cao',
  uncertain: 'Chưa chắc chắn, nên kiểm tra lại',
  low: 'Không đủ tin cậy, đừng dựa vào câu trả lời này',
};

export const LEVEL_EARCON: Record<UncertaintyLevel, EarconName> = {
  confident: 'done',
  uncertain: 'uncertain',
  low: 'low',
};

const LEVEL_SPEECH: Record<UncertaintyLevel, string> = {
  confident: '',
  uncertain: 'AI chưa chắc chắn. ',
  low: 'AI không đủ tin cậy, hãy kiểm tra lại. ',
};

export function AskDialog({ open, onClose, block, index, total, docId, speak }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { play } = useEarcons();
  const [question, setQuestion] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<VqaResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setResult(null);
      setError('');
      dialog.showModal();
      inputRef.current?.focus();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const canAsk = Boolean(image || (docId && block));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = question.trim();
    if (text.length < 2) {
      setError('Hãy nhập câu hỏi.');
      return;
    }
    if (!canAsk) {
      setError('Hãy tải một tài liệu lên hoặc chọn một ảnh để hỏi.');
      return;
    }
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const answer = await askVqa(
        image ? { question: text, image } : { question: text, documentId: docId, blockId: block?.id },
      );
      setResult(answer);
      const earconMs = play(LEVEL_EARCON[answer.uncertainty_level]);
      speak(`${LEVEL_SPEECH[answer.uncertainty_level]}${answer.answer}`, earconMs); // chờ âm báo xong rồi mới đọc
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không hỏi được AI');
      play('error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby="ask-title"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
      className="max-h-[92vh] w-[94vw] max-w-3xl overflow-auto rounded-xl border-[6px] border-ac bg-bg p-6 text-fg backdrop:bg-black/70"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 id="ask-title" className="text-2xl font-extrabold text-ac">
          Hỏi đáp AI
        </h2>
        <button type="button" className="btn btn-primary" onClick={onClose}>
          Đóng (Esc)
        </button>
      </div>

      <p className="mt-2 font-bold">
        {image
          ? `Hỏi về ảnh: ${image.name}`
          : block
            ? `Mục đang chọn: ${TYPE_LABEL[block.type]} ${index + 1}/${total}`
            : 'Chưa chọn mục nào'}
      </p>

      <form onSubmit={submit} className="mt-4 flex flex-col gap-3">
        <label htmlFor="ask-input" className="font-bold">
          Câu hỏi
        </label>
        <input
          id="ask-input"
          ref={inputRef}
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ví dụ: Tổng doanh thu quý 3 là bao nhiêu?"
          className="w-full rounded-md border-[3px] border-fg bg-bg px-3 py-3 text-lg text-fg"
          autoComplete="off"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang hỏi...' : 'Hỏi (Enter)'}
          </button>
          <label className="btn cursor-pointer">
            {image ? 'Đổi ảnh' : 'Hoặc chọn ảnh để hỏi trực tiếp'}
            <input
              type="file"
              className="sr-only"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
            />
          </label>
          {image && (
            <button type="button" className="btn" onClick={() => setImage(null)}>
              Bỏ ảnh
            </button>
          )}
        </div>
      </form>

      <div role="status" aria-live="polite" className="mt-5">
        {busy && <p className="font-bold">AI đang đọc tài liệu, vui lòng chờ...</p>}
        {error && (
          <p className="rounded-md border-[3px] border-dashed border-fg p-3 font-bold text-ac" role="alert">
            Lỗi: {error}
          </p>
        )}
        {result && (
          <section aria-label="Câu trả lời" className="rounded-md border-[3px] border-fg bg-pane p-4">
            <p className="text-xl font-extrabold">{result.answer}</p>
            <p className="mt-3 border-2 border-dashed border-fg p-2 font-bold">
              {result.uncertainty_level === 'confident' ? '✓ ' : '⚠ '}
              {LEVEL_LABEL[result.uncertainty_level]} ({Math.round(result.confidence * 100)}%)
            </p>
            {result.reason_texts.length > 0 && (
              <ul className="mt-2 list-disc pl-6 font-bold">
                {result.reason_texts.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}
            <div className="mt-3">
              <button
                type="button"
                className="btn"
                onClick={() => speak(`${LEVEL_SPEECH[result.uncertainty_level]}${result.answer}`)}
              >
                Đọc lại câu trả lời
              </button>
            </div>
          </section>
        )}
      </div>
    </dialog>
  );
}
