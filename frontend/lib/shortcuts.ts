export type ShortcutItem = {
  keys: string[];
  label: string;
  pending?: boolean;
};

export type ShortcutGroup = {
  group: string;
  items: ShortcutItem[];
};

export const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    group: 'Điều hướng',
    items: [
      { keys: ['J', '↓'], label: 'Đoạn kế tiếp' },
      { keys: ['K', '↑'], label: 'Đoạn trước' },
      { keys: ['H'], label: 'Tiêu đề kế tiếp (Shift+H: trước đó)' },
      { keys: ['G'], label: 'Hình hoặc biểu đồ kế tiếp (Shift+G: trước đó)' },
      { keys: ['T'], label: 'Bảng kế tiếp (Shift+T: trước đó)' },
    ],
  },
  {
    group: 'Đọc',
    items: [
      { keys: ['Space'], label: 'Phát hoặc tạm dừng' },
      { keys: ['R'], label: 'Đọc lại đoạn hiện tại' },
      { keys: ['←', '→'], label: 'Lùi hoặc tới một câu' },
      { keys: ['[', ']'], label: 'Giảm hoặc tăng tốc độ đọc' },
      { keys: ['S'], label: 'Dừng đọc' },
    ],
  },
  {
    group: 'Hiển thị',
    items: [
      { keys: ['C'], label: 'Đổi chế độ tương phản' },
      { keys: ['+', '-'], label: 'Phóng to hoặc thu nhỏ' },
      { keys: ['Z'], label: 'Bật hoặc tắt zoom bám vùng đọc' },
      { keys: ['0'], label: 'Đặt lại zoom về 100%' },
      { keys: ['L'], label: 'Đổi kiểu zoom' },
    ],
  },
  {
    group: 'Giọng nói và AI',
    items: [
      { keys: ['D'], label: 'Mô tả hình đang chọn' },
      { keys: ['M'], label: 'Bật hoặc tắt micro', pending: true },
      { keys: ['Q'], label: 'Hỏi đáp về mục đang chọn', pending: true },
      { keys: ['U'], label: 'Nhảy tới cảnh báo AI gần nhất', pending: true },
    ],
  },
  {
    group: 'Chung',
    items: [
      { keys: ['F1', '?'], label: 'Mở bảng phím tắt' },
      { keys: ['Esc'], label: 'Đóng hộp thoại, trả focus về vị trí trước đó' },
    ],
  },
];
