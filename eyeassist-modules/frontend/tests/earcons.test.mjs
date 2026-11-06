// Chạy: node --test frontend/tests/earcons.test.mjs   (Node >= 18, không cần trình duyệt)
import test from "node:test";
import assert from "node:assert/strict";
import { EarconPlayer, EARCON_DEFS } from "../src/lib/audio/earcons.js";

function fakeAudioContext() {
  const log = { oscillators: [], connects: 0 };
  const param = () => ({
    value: 0,
    setValueAtTime() {}, exponentialRampToValueAtTime() {},
    linearRampToValueAtTime() {}, cancelScheduledValues() {},
  });
  const node = () => ({ connect() { log.connects++; }, gain: param(), frequency: param() });
  return {
    log,
    ctx: {
      currentTime: 0, state: "running", destination: {},
      resume: async () => {},
      createGain: node,
      createBiquadFilter: () => ({ ...node(), type: "", frequency: { value: 0 } }),
      createOscillator: () => {
        const o = { ...node(), type: "", frequency: param(), start() {}, stop() { o.stopped = true; } };
        log.oscillators.push(o);
        return o;
      },
    },
  };
}

const make = (opts = {}) => {
  const f = fakeAudioContext();
  return { p: new EarconPlayer({ audioContextFactory: () => f.ctx, ...opts }), log: f.log };
};

test("bảng định nghĩa khớp ma trận đã thiết kế", () => {
  const D = EARCON_DEFS;
  assert.deepEqual(D.chartDetected.notes.map((n) => n.freq), [660, 880]);
  assert.deepEqual(D.regionChange.notes.map((n) => n.freq), [520]);
  assert.deepEqual(D.error.notes.map((n) => n.freq), [330, 220]);
  assert.deepEqual(D.aiUncertain.notes.map((n) => n.freq), [740, 740, 740]);
});

test("thời lượng đúng", () => {
  const { p } = make();
  assert.equal(p.play("chartDetected"), 300);
  const q = make().p;
  assert.equal(q.play("regionChange"), 70);
  assert.equal(make().p.play("error"), 350);
  assert.equal(make().p.play("aiUncertain"), 360); // nốt cuối bắt đầu ở 280 ms, dài 80 ms
});

test("tắt âm thì không phát", () => {
  const { p, log } = make({ enabled: false });
  assert.equal(p.play("error"), 0);
  assert.equal(log.oscillators.length, 0);
});

test("chuyển vùng liên tục trong 150 ms chỉ phát một lần", () => {
  const { p } = make();
  assert.equal(p.play("regionChange"), 70);
  assert.equal(p.play("regionChange"), 0);
});

test("âm ưu tiên thấp không chen vào âm ưu tiên cao đang phát", () => {
  const { p } = make();
  assert.equal(p.play("error"), 350);
  assert.equal(p.play("aiUncertain"), 0);
  assert.equal(p.play("chartDetected"), 0);
});

test("âm ưu tiên cao cắt âm ưu tiên thấp đang phát", () => {
  const { p, log } = make();
  p.play("chartDetected");
  assert.equal(p.play("error"), 350);
  assert.ok(log.oscillators.slice(0, 2).every((o) => o.stopped));
});

test("playThen gọi TTS sau khi earcon kết thúc", async () => {
  const { p } = make();
  const t0 = Date.now();
  let spokenAt = 0;
  await p.playThen("regionChange", () => { spokenAt = Date.now(); }, 20);
  assert.ok(spokenAt - t0 >= 85, `TTS gọi quá sớm: ${spokenAt - t0} ms`);
});

test("describe liệt kê đủ 4 âm", () => {
  const text = make().p.describe();
  for (const s of ["Phát hiện biểu đồ", "Chuyển vùng đọc", "Báo lỗi", "AI không chắc chắn"]) {
    assert.ok(text.includes(s));
  }
});
