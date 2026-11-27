export type BlockType = 'heading' | 'paragraph' | 'figure' | 'table';

export type FigureCrop = {
  url: string;
  pw: number;
  ph: number;
  x: number;
  y: number;
  w: number;
  h: number;
};

export type Block = {
  id: string;
  type: BlockType;
  text: string;
  speech: string;
  confidence?: number;
  aiDescription?: boolean;
  crop?: FigureCrop;
  level?: number;
  description?: string;
  rows?: string[][];
  chart?: { label: string; value: number }[];
};

export const TYPE_LABEL: Record<BlockType, string> = {
  heading: 'Tiêu đề',
  paragraph: 'Đoạn văn',
  figure: 'Hình',
  table: 'Bảng',
};
