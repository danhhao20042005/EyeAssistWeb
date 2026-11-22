// Chạy: npm test   (Node >= 22.6, không cần trình duyệt, không cần cài thêm gói nào)
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  EARCON_GAP_MS,
  SPEECH_GAP_MS,
  createAfterEarcon,
  patternDurationMs,
  planSequence,
  speechDelayMs,
  warningEarcon,
} from '../lib/earconSync';
import { CONFIDENT_THRESHOLD, LOW_THRESHOLD, levelOf } from '../lib/thresholds';

// ---------- bộ hẹn giờ giả để kiểm tra thứ tự mà không phải chờ thật ----------
function fakeTimer() {
  let now = 0;
  let nextId = 1;
  const jobs = new Map<number, { at: number; fn: () => void }>();
  return {
    timer: {
      set: (fn: () => void, ms: number) => {
        const id = nextId++;
        jobs.set(id, { at: now + ms, fn });
        return id;
      },
      clear: (id: unknown) => void jobs.delete(id as number),
    },
    advance(ms: number) {
      const end = now + ms;
      for (;;) {
        const due = [...jobs.entries()].filter(([, j]) => j.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!due) break;
        now = due[1].at;
        jobs.delete(due[0]);
        due[1].fn();
      }
      now = end;
    },
    pending: () => jobs.size,
  };
}

test('thời lượng mẫu âm = nốt kết thúc muộn nhất', () => {
  assert.equal(patternDurationMs([{ start: 0, dur: 0.12 }, { start: 0.12, dur: 0.18 }]), 300);
  assert.equal(patternDurationMs([{ start: 0, dur: 0.1 }, { start: 0.1, dur: 0.22 }]), 320);
  assert.equal(patternDurationMs([]), 0);
});

test('xếp chuỗi âm báo nối đuôi, có khoảng nghỉ', () => {
  const { steps, totalMs } = planSequence([
    { name: 'heading', durationMs: 100 },
    { name: 'uncertain', durationMs: 420 },
  ]);
  assert.deepEqual(steps.map((s) => [s.name, s.offsetMs]), [['heading', 0], ['uncertain', 100 + EARCON_GAP_MS]]);
  assert.equal(totalMs, 100 + EARCON_GAP_MS + 420);
  assert.deepEqual(planSequence([]), { steps: [], totalMs: 0 });
  assert.equal(planSequence([{ name: 'a', durationMs: 50 }]).totalMs, 50); // một âm: không cộng khoảng nghỉ thừa
});

test('giọng đọc chờ âm báo xong cộng khoảng nghỉ; không có âm báo thì đọc ngay', () => {
  assert.equal(speechDelayMs(420), 420 + SPEECH_GAP_MS);
  assert.equal(speechDelayMs(0), 0);
});

test('createAfterEarcon: đọc sau khi âm báo xong, không sớm hơn', () => {
  const ft = fakeTimer();
  const gate = createAfterEarcon(ft.timer);
  const log: string[] = [];
  gate.run(420, () => log.push('đọc'));
  assert.ok(gate.isWaiting());
  ft.advance(420 + SPEECH_GAP_MS - 1);
  assert.deepEqual(log, []);           // âm báo còn đang phát hoặc đang nghỉ: chưa đọc
  ft.advance(1);
  assert.deepEqual(log, ['đọc']);
  assert.ok(!gate.isWaiting());
});

test('createAfterEarcon: không âm báo thì đọc ngay lập tức', () => {
  const gate = createAfterEarcon(fakeTimer().timer);
  let spoke = false;
  gate.run(0, () => { spoke = true; });
  assert.ok(spoke);
});

test('chuyển vùng liên tục: chỉ đọc khối cuối, không còn bộ hẹn giờ mồ côi', () => {
  const ft = fakeTimer();
  const gate = createAfterEarcon(ft.timer);
  const spoken: string[] = [];
  gate.run(300, () => spoken.push('khối 1'));
  ft.advance(100);
  gate.run(300, () => spoken.push('khối 2'));
  ft.advance(100);
  gate.run(300, () => spoken.push('khối 3'));
  ft.advance(5000);
  assert.deepEqual(spoken, ['khối 3']);
  assert.equal(ft.pending(), 0);
});

test('huỷ giữa chừng (dừng đọc / chuyển vùng) thì không đọc nữa', () => {
  const ft = fakeTimer();
  const gate = createAfterEarcon(ft.timer);
  let spoke = false;
  gate.run(300, () => { spoke = true; });
  gate.cancel();
  ft.advance(5000);
  assert.ok(!spoke && ft.pending() === 0);
});

test('mô phỏng lỗi cũ: setTimeout cảnh báo 350 ms không bị huỷ sẽ phát nhầm; cơ chế mới thì không', () => {
  // Cách cũ: sau khi vào khối A (độ tin cậy thấp), hẹn phát âm cảnh báo sau 350 ms bằng setTimeout rời.
  const ft = fakeTimer();
  const played: string[] = [];
  const oldWay = (name: string) => ft.timer.set(() => played.push(`cảnh báo ${name}`), 350);
  oldWay('A');
  ft.advance(200);            // người dùng đã sang khối B (tin cậy cao)
  ft.advance(200);
  assert.deepEqual(played, ['cảnh báo A']); // âm cảnh báo của khối A vang lên khi đã ở khối B: sai

  // Cách mới: cảnh báo nằm trong cùng chuỗi âm báo và bị huỷ cùng giọng đọc.
  const gate = createAfterEarcon(ft.timer);
  const spoken: string[] = [];
  gate.run(620, () => spoken.push('A'));
  ft.advance(200);
  gate.run(100, () => spoken.push('B'));
  ft.advance(5000);
  assert.deepEqual(spoken, ['B']);
});

test('âm cảnh báo theo ngưỡng 0,85 / 0,60 của báo cáo', () => {
  const c = CONFIDENT_THRESHOLD, l = LOW_THRESHOLD;
  assert.equal(warningEarcon(0.9, c, l), null);
  assert.equal(warningEarcon(0.85, c, l), null);
  assert.equal(warningEarcon(0.84, c, l), 'uncertain');
  assert.equal(warningEarcon(0.6, c, l), 'uncertain');
  assert.equal(warningEarcon(0.59, c, l), 'low');
  assert.equal(warningEarcon(undefined, c, l), null);
  assert.equal(warningEarcon(Number.NaN, c, l), null);
});

test('levelOf khớp backend uncertainty_level và nhận ngưỡng tuỳ chỉnh (ví dụ T_conf = 0,70)', () => {
  assert.deepEqual([0.85, 0.84, 0.6, 0.59].map((v) => levelOf(v)), ['confident', 'uncertain', 'uncertain', 'low']);
  assert.equal(levelOf(0.72, 0.7, 0.5), 'confident');
  assert.equal(levelOf(0.69, 0.7, 0.5), 'uncertain');
});
