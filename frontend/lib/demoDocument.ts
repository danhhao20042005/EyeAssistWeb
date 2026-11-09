export type BlockType = 'heading' | 'paragraph' | 'figure' | 'table';

export type Block = {
  id: string;
  type: BlockType;
  text: string;
  speech: string;
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

const tableRows = [
  ['Mảng', 'Quý 2', 'Quý 3', 'Tăng'],
  ['Dịch vụ trực tuyến', '48 tỷ', '62 tỷ', '29%'],
  ['Bán lẻ', '40 tỷ', '41 tỷ', '3%'],
  ['Khác', '16 tỷ', '17 tỷ', '6%'],
];

function describeTable(rows: string[][]): string {
  const [head, ...body] = rows;
  const lines = body.map((r) => r.map((cell, i) => `${head[i]}: ${cell}`).join(', '));
  return `Bảng ${head.length} cột, ${body.length} hàng. ${lines.join('. ')}.`;
}

export const DEMO_BLOCKS: Block[] = [
  {
    id: 'b1',
    type: 'heading',
    level: 1,
    text: 'Báo cáo kết quả kinh doanh quý 3',
    speech: 'Báo cáo kết quả kinh doanh quý 3.',
  },
  {
    id: 'b2',
    type: 'heading',
    level: 2,
    text: '1. Giới thiệu',
    speech: 'Mục một. Giới thiệu.',
  },
  {
    id: 'b3',
    type: 'paragraph',
    text: 'Tài liệu này tóm tắt kết quả kinh doanh của công ty trong ba quý đầu năm. Các số liệu được tổng hợp từ báo cáo nội bộ và đã được phòng tài chính xác nhận.',
    speech:
      'Tài liệu này tóm tắt kết quả kinh doanh của công ty trong ba quý đầu năm. Các số liệu được tổng hợp từ báo cáo nội bộ và đã được phòng tài chính xác nhận.',
  },
  {
    id: 'b4',
    type: 'heading',
    level: 2,
    text: '2. Doanh thu quý 3',
    speech: 'Mục hai. Doanh thu quý 3.',
  },
  {
    id: 'b5',
    type: 'paragraph',
    text: 'Quý 3 đạt 120 tỷ đồng, cao hơn quý 2 khoảng 15%, chủ yếu nhờ mảng dịch vụ trực tuyến. Biểu đồ bên dưới minh họa doanh thu theo từng quý.',
    speech:
      'Quý 3 đạt 120 tỷ đồng, cao hơn quý 2 khoảng 15%, chủ yếu nhờ mảng dịch vụ trực tuyến. Biểu đồ bên dưới minh họa doanh thu theo từng quý.',
  },
  {
    id: 'b6',
    type: 'figure',
    text: 'Biểu đồ cột: doanh thu theo quý',
    speech: 'Hình. Biểu đồ cột doanh thu theo quý. Nhấn D để nghe mô tả.',
    description:
      'Biểu đồ cột gồm ba cột cho quý 1, quý 2 và quý 3. Doanh thu tăng đều qua từng quý, từ 85 tỷ lên 104 tỷ rồi 120 tỷ đồng. Cột quý 3 cao nhất.',
    chart: [
      { label: 'Quý 1', value: 85 },
      { label: 'Quý 2', value: 104 },
      { label: 'Quý 3', value: 120 },
    ],
  },
  {
    id: 'b7',
    type: 'heading',
    level: 2,
    text: '3. Doanh thu theo mảng',
    speech: 'Mục ba. Doanh thu theo mảng.',
  },
  {
    id: 'b8',
    type: 'table',
    text: 'Bảng doanh thu theo mảng, quý 2 và quý 3',
    speech: describeTable(tableRows),
    rows: tableRows,
  },
  {
    id: 'b9',
    type: 'paragraph',
    text: 'Mảng dịch vụ trực tuyến tăng mạnh nhất, trong khi mảng bán lẻ gần như đi ngang. Chi phí vận hành quý 3 tăng nhẹ so với quý 2.',
    speech:
      'Mảng dịch vụ trực tuyến tăng mạnh nhất, trong khi mảng bán lẻ gần như đi ngang. Chi phí vận hành quý 3 tăng nhẹ so với quý 2.',
  },
  {
    id: 'b10',
    type: 'heading',
    level: 2,
    text: '4. Kết luận',
    speech: 'Mục bốn. Kết luận.',
  },
  {
    id: 'b11',
    type: 'paragraph',
    text: 'Công ty duy trì đà tăng trưởng trong quý 3. Kế hoạch quý 4 tập trung mở rộng dịch vụ trực tuyến và kiểm soát chi phí.',
    speech:
      'Công ty duy trì đà tăng trưởng trong quý 3. Kế hoạch quý 4 tập trung mở rộng dịch vụ trực tuyến và kiểm soát chi phí.',
  },
];
