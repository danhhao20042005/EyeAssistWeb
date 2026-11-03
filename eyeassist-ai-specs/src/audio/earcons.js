// EyeAssist - Earcons (Web Audio API)
// 4 sự kiện: chartDetected, regionChange, error, aiUncertain

const ctx = new (window.AudioContext || window.webkitAudioContext)();

// Trình duyệt chặn âm thanh đến khi có thao tác người dùng.
// Gọi hàm này trong sự kiện phím/click đầu tiên.
export function unlockAudio() {
  if (ctx.state === "suspended") ctx.resume();
}

function tone({
  freq, start, dur, type = "sine", gain = 0.2,
  glideTo = null, vibrato = null, lowpass = null,
}) {
  const t0 = ctx.currentTime + start;
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  if (glideTo) osc.frequency.linearRampToValueAtTime(glideTo, t0 + dur);

  // Envelope để tránh tiếng "click" khi bật/tắt
  amp.gain.setValueAtTime(0.0001, t0);
  amp.gain.exponentialRampToValueAtTime(gain, t0 + 0.01);
  amp.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);

  let node = osc;
  if (lowpass) {
    const f = ctx.createBiquadFilter();
    f.type = "lowpass";
    f.frequency.value = lowpass;
    osc.connect(f);
    node = f;
  }
  node.connect(amp).connect(ctx.destination);

  if (vibrato) {
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.value = vibrato.rate;
    lfoGain.gain.value = vibrato.depth;
    lfo.connect(lfoGain).connect(osc.frequency);
    lfo.start(t0);
    lfo.stop(t0 + dur);
  }
  osc.start(t0);
  osc.stop(t0 + dur + 0.02);
}

export const earcons = {
  // 660 -> 880 Hz, 120 + 180 ms, sine
  chartDetected() {
    tone({ freq: 660, start: 0, dur: 0.12, gain: 0.25 });
    tone({ freq: 880, start: 0.12, dur: 0.18, gain: 0.25 });
  },
  // 520 Hz, 70 ms, triangle
  regionChange() {
    tone({ freq: 520, start: 0, dur: 0.07, type: "triangle", gain: 0.15 });
  },
  // 330 -> 220 Hz, 150 + 200 ms, square + lowpass 1200 Hz
  error() {
    tone({ freq: 330, start: 0, dur: 0.15, type: "square", gain: 0.2, lowpass: 1200 });
    tone({ freq: 220, start: 0.15, dur: 0.2, type: "square", gain: 0.2, lowpass: 1200 });
  },
  // 740 Hz x3, 80 ms, cách nhau 60 ms, vibrato 6 Hz +-12 Hz
  aiUncertain() {
    for (let i = 0; i < 3; i++) {
      tone({ freq: 740, start: i * 0.14, dur: 0.08, gain: 0.2,
             vibrato: { rate: 6, depth: 12 } });
    }
  },
};
