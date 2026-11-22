import test from 'node:test';
import assert from 'node:assert/strict';

// AudioContext giả ghi lại lịch phát của từng bộ dao động.
type Osc = { freq: number; startAt: number; stopAt: number; stopped: boolean };
const oscillators: Osc[] = [];
let currentTime = 0;

class FakeAudioContext {
  state = 'running';
  destination = {};
  get currentTime() { return currentTime; }
  resume() { return Promise.resolve(); }
  createGain() {
    const param = { value: 0, setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {}, cancelScheduledValues() {}, setTargetAtTime() {} };
    return { gain: param, connect() {} };
  }
  createOscillator() {
    const rec: Osc = { freq: 0, startAt: -1, stopAt: -1, stopped: false };
    oscillators.push(rec);
    return {
      type: 'sine',
      frequency: { setValueAtTime: (f: number) => { rec.freq = f; }, linearRampToValueAtTime() {} },
      connect() {},
      onended: null as null | (() => void),
      start: (t: number) => { rec.startAt = t; },
      stop: (t: number) => { rec.stopAt = t; rec.stopped = true; },
    };
  }
}
(globalThis as unknown as { window: unknown }).window = { AudioContext: FakeAudioContext };

const { earconPlayer, earconDurationMs, EARCON_LABEL } = await import('../lib/earcons');
import { createAfterEarcon, SPEECH_GAP_MS } from '../lib/earconSync';

test('thời lượng từng âm báo (ms) khớp bảng thiết kế', () => {
  const expected = { ready: 300, done: 320, heading: 100, paragraph: 50, figure: 260, table: 270, uncertain: 420, low: 580, error: 320 };
  for (const [name, ms] of Object.entries(expected)) {
    assert.equal(earconDurationMs(name as keyof typeof expected), ms, name);
  }
  assert.equal(earconDurationMs('processing'), 0);
  assert.ok(EARCON_LABEL.uncertain && EARCON_LABEL.low);
});

test('play trả về thời lượng và hẹn đúng số nốt', () => {
  oscillators.length = 0;
  assert.equal(earconPlayer.play('low'), 580);
  assert.deepEqual(oscillators.map((o) => Math.round(o.freq)), [659, 523, 392]);
  assert.equal(earconPlayer.play('processing'), 0);
  earconPlayer.stopProcessing();
});

test('playSequence: âm cảnh báo bắt đầu sau âm loại khối + khoảng nghỉ, tổng thời lượng đúng', () => {
  oscillators.length = 0;
  const total = earconPlayer.playSequence(['heading', 'uncertain']);
  assert.equal(total, 100 + 100 + 420);
  const [heading, warn1, warn2] = oscillators;
  const gapS = (warn1.startAt - heading.startAt);
  assert.ok(Math.abs(gapS - 0.2) < 1e-9, `lệch ${gapS}`);          // 100 ms âm heading + 100 ms nghỉ
  assert.ok(Math.abs(warn2.startAt - warn1.startAt - 0.18) < 1e-9); // nốt thứ hai của "uncertain"
});

test('cancel dừng mọi âm đã hẹn (chuyển vùng nhanh không để âm cũ vang lên)', () => {
  oscillators.length = 0;
  earconPlayer.playSequence(['figure', 'low']);
  assert.ok(oscillators.length >= 6 && oscillators.every((o) => !o.stopped || o.stopAt > 0));
  const before = oscillators.map((o) => o.stopAt);
  currentTime = 0.05;
  earconPlayer.cancel();
  currentTime = 0;
  assert.ok(oscillators.every((o, i) => o.stopAt <= before[i]), 'mọi bộ dao động phải được hẹn dừng sớm');
  assert.ok(oscillators.every((o) => o.stopAt <= 0.1 + 1e-9));
});

test('tích hợp: âm báo rồi mới đến giọng đọc, và giọng đọc cũ không chen vào khi chuyển vùng nhanh', () => {
  let now = 0;
  const jobs: { at: number; fn: () => void }[] = [];
  const timer = {
    set: (fn: () => void, ms: number) => { const j = { at: now + ms, fn }; jobs.push(j); return j; },
    clear: (id: unknown) => { const i = jobs.indexOf(id as (typeof jobs)[number]); if (i >= 0) jobs.splice(i, 1); },
  };
  const advance = (ms: number) => {
    const end = now + ms;
    while (jobs.length) {
      jobs.sort((a, b) => a.at - b.at);
      if (jobs[0].at > end) break;
      const j = jobs.shift()!; now = j.at; j.fn();
    }
    now = end;
  };
  const gate = createAfterEarcon(timer);
  const events: string[] = [];

  // Điều hướng tới một khối có OCR không chắc chắn: âm loại khối + âm cảnh báo, rồi đọc
  const navigate = (label: string, names: Parameters<typeof earconPlayer.playSequence>[0]) => {
    earconPlayer.cancel();
    const ms = earconPlayer.playSequence(names);
    events.push(`${label}: âm báo ${ms} ms @${now}`);
    gate.run(ms, () => events.push(`${label}: bắt đầu đọc @${now}`));
  };

  navigate('A', ['paragraph', 'low']);
  advance(100);
  navigate('B', ['heading']);
  advance(5000);
  assert.deepEqual(events, [
    'A: âm báo 730 ms @0',
    'B: âm báo 100 ms @100',
    `B: bắt đầu đọc @${100 + 100 + SPEECH_GAP_MS}`,
  ]);
});
