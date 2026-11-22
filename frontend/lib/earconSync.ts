// Logic thuần (không phụ thuộc React/Web Audio) để đồng bộ âm báo phi ngôn ngữ với giọng đọc.
// Tách riêng để kiểm thử bằng `npm test` mà không cần trình duyệt.

/** Khoảng nghỉ giữa lúc âm báo kết thúc và lúc giọng đọc bắt đầu, để hai kênh không chồng lên nhau. */
export const SPEECH_GAP_MS = 120;
/** Khoảng nghỉ giữa hai âm báo liền nhau (âm loại khối rồi âm cảnh báo). */
export const EARCON_GAP_MS = 100;

export type ToneSpec = { start: number; dur: number };

export function patternDurationMs(tones: ToneSpec[]): number {
  if (!tones.length) return 0;
  return Math.round(Math.max(...tones.map((t) => t.start + t.dur)) * 1000);
}

export type SequenceStep = { name: string; offsetMs: number; durationMs: number };

/** Xếp các âm báo nối đuôi nhau; offset tính từ lúc bắt đầu chuỗi. */
export function planSequence(
  items: { name: string; durationMs: number }[],
  gapMs: number = EARCON_GAP_MS,
): { steps: SequenceStep[]; totalMs: number } {
  const steps: SequenceStep[] = [];
  let cursor = 0;
  for (const item of items) {
    steps.push({ name: item.name, offsetMs: cursor, durationMs: item.durationMs });
    cursor += item.durationMs + gapMs;
  }
  return { steps, totalMs: steps.length ? cursor - gapMs : 0 };
}

/** Độ trễ giọng đọc sau một âm báo dài `earconMs`. Không có âm báo thì đọc ngay. */
export function speechDelayMs(earconMs: number, gapMs: number = SPEECH_GAP_MS): number {
  return earconMs > 0 ? earconMs + gapMs : 0;
}

export type Timer = {
  set: (fn: () => void, ms: number) => unknown;
  clear: (id: unknown) => void;
};

const defaultTimer: Timer = {
  set: (fn, ms) => setTimeout(fn, ms),
  clear: (id) => clearTimeout(id as ReturnType<typeof setTimeout>),
};

/**
 * Chạy `fn` (bắt đầu đọc) sau khi âm báo xong. Mỗi lần gọi run() hoặc cancel() sẽ huỷ lần chờ trước,
 * nên bấm phím chuyển vùng liên tục không để lại bộ hẹn giờ "mồ côi" đọc nhầm nội dung cũ.
 */
export function createAfterEarcon(timer: Timer = defaultTimer, gapMs: number = SPEECH_GAP_MS) {
  let pending: unknown = null;
  let epoch = 0;

  function cancel() {
    epoch += 1;
    if (pending !== null) {
      timer.clear(pending);
      pending = null;
    }
  }

  function run(earconMs: number, fn: () => void) {
    cancel();
    const mine = epoch;
    const delay = speechDelayMs(earconMs, gapMs);
    if (delay <= 0) {
      fn();
      return;
    }
    pending = timer.set(() => {
      pending = null;
      if (mine === epoch) fn();
    }, delay);
  }

  return { run, cancel, isWaiting: () => pending !== null };
}

/** Âm cảnh báo đi kèm một khối có độ tin cậy OCR thấp; null nếu không cần cảnh báo. */
export function warningEarcon(
  confidence: number | undefined,
  confident: number,
  low: number,
): 'uncertain' | 'low' | null {
  if (confidence === undefined || Number.isNaN(confidence)) return null;
  if (confidence >= confident) return null;
  return confidence >= low ? 'uncertain' : 'low';
}
