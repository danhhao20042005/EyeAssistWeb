import { TYPE_LABEL, type Block, type BlockType } from '@/lib/types';

export const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 0) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export type ApiBlock = {
  id: string;
  type: BlockType;
  page: number;
  bbox: { x: number; y: number; w: number; h: number };
  text: string;
  confidence: number;
  order: number;
  level: number | null;
  rows: string[][] | null;
};

export type ApiPage = { index: number; width: number; height: number; blocks: ApiBlock[] };

export type ApiDocument = {
  id: string;
  filename: string;
  page_count: number;
  pages: ApiPage[];
  reading_order: string[];
  warnings: string[];
  ocr_engine: string;
  layout_engine: string;
};

export type ApiJob = {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error: string | null;
  result: ApiDocument | null;
};

export type UncertaintyLevel = 'confident' | 'uncertain' | 'low';

export type VqaResult = {
  answer: string;
  confidence: number;
  uncertainty_level: UncertaintyLevel;
  reasons: string[];
  reason_texts: string[];
  evidence_region: { page: number; x: number; y: number; w: number; h: number } | null;
  raw_ocr_text: string | null;
  engine: string;
};

async function send(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(`Không kết nối được máy chủ. Hãy chạy backend tại ${API_BASE}`);
  }
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Máy chủ báo lỗi (mã ${response.status})`;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') message = body.detail;
      else if (Array.isArray(body?.detail)) message = 'Yêu cầu gửi lên không hợp lệ';
    } catch {}
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export async function uploadDocument(file: File): Promise<ApiJob> {
  const form = new FormData();
  form.append('file', file);
  return readJson<ApiJob>(await send('/api/documents', { method: 'POST', body: form }));
}

export async function getDocument(id: string): Promise<ApiJob> {
  return readJson<ApiJob>(await send(`/api/documents/${id}`));
}

export type AskInput = {
  question: string;
  documentId?: string;
  blockId?: string;
  image?: File;
};

export async function askVqa(input: AskInput): Promise<VqaResult> {
  const form = new FormData();
  form.append('question', input.question);
  if (input.image) {
    form.append('image', input.image);
  } else if (input.documentId && input.blockId) {
    form.append('document_id', input.documentId);
    form.append('block_id', input.blockId);
  }
  return readJson<VqaResult>(await send('/api/vqa', { method: 'POST', body: form }));
}

export function pageImageUrl(documentId: string, pageIndex: number): string {
  return `${API_BASE}/api/documents/${documentId}/pages/${pageIndex}/image`;
}

function rectangular(rows: string[][]): string[][] {
  const cols = Math.max(0, ...rows.map((row) => row.length));
  return rows.map((row) => Array.from({ length: cols }, (_, i) => (row[i] ?? '').trim()));
}

function speakTable(rows: string[][]): string {
  const [head, ...body] = rows;
  const names = (head ?? []).map((cell, i) => cell || `${TYPE_LABEL.table} ${i + 1}`);
  const lines = body.map((row) =>
    row
      .map((cell, i) => `${names[i]}: ${cell || 'trống'}`)
      .join(', '),
  );
  return `Bảng ${names.length} cột, ${body.length} hàng. ${lines.join('. ')}${lines.length ? '.' : ''}`;
}

function toBlock(block: ApiBlock, page: ApiPage, documentId: string): Block {
  const base = { id: block.id, type: block.type, confidence: block.confidence };
  const text = block.text.trim();

  if (block.type === 'heading') {
    return { ...base, level: block.level ?? 2, text, speech: `${text}.` };
  }
  if (block.type === 'figure') {
    return {
      ...base,
      text: `Hình trên trang ${page.index + 1}`,
      speech: `Hình trên trang ${page.index + 1}. Nhấn D để nghe mô tả.`,
      crop: {
        url: pageImageUrl(documentId, page.index),
        pw: page.width,
        ph: page.height,
        x: block.bbox.x,
        y: block.bbox.y,
        w: block.bbox.w,
        h: block.bbox.h,
      },
    };
  }
  if (block.type === 'table') {
    const rows = block.rows && block.rows.length ? rectangular(block.rows) : [];
    if (rows.length && rows[0].length) {
      const caption = `Bảng ${rows[0].length} cột, ${rows.length - 1} hàng`;
      return { ...base, text: caption, speech: speakTable(rows), rows };
    }
    const empty = 'Bảng chưa nhận dạng được nội dung';
    return { ...base, text: empty, speech: `${empty}.` };
  }
  return { ...base, text, speech: text };
}

export function toBlocks(document: ApiDocument): Block[] {
  const lookup = new Map<string, { block: ApiBlock; page: ApiPage }>();
  for (const page of document.pages) {
    for (const block of page.blocks) lookup.set(block.id, { block, page });
  }
  const result: Block[] = [];
  for (const id of document.reading_order) {
    const entry = lookup.get(id);
    if (entry) result.push(toBlock(entry.block, entry.page, document.id));
  }
  return result;
}
