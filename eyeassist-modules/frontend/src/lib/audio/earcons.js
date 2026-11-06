// EyeAssist - Bộ phát âm báo Earcons (Web Audio API)
//
// 4 sự kiện: chartDetected, regionChange, error, aiUncertain
// Tính năng: ưu tiên âm, chống lặp, âm lượng/tắt-bật riêng, phát trước TTS.
// An toàn với Next.js SSR: AudioContext chỉ được tạo trên trình duyệt, khi cần.

/** Định nghĩa từng earcon. Đơn vị: giây, Hz. */
export const EARCON_DEFS = {
  chartDetected: {
    priority: 2,
    label: "Phát hiện biểu đồ",
    help: "hai nốt đi lên",
    notes: [
      { freq: 660, start: 0.0, dur: 0.12, type: "sine", gain: 0.25 },
      { freq: 880, start: 0.12, dur: 0.18, type: "sine", gain: 0.25 },
    ],
  },
  regionChange: {
    priority: 1,
    label: "Chuyển vùng đọc",
    help: "một tiếng tích ngắn",
    debounceMs: 150, // bỏ qua nếu lặp trong 150 ms (duyệt nhanh bằng phím tắt)
    notes: [{ freq: 520, start: 0, dur: 0.07, type: "triangle", gain: 0.15 }],
  },
  error: {
    priority: 4,
    label: "Báo lỗi",
    help: "hai nốt trầm đi xuống",
    notes: [
      { freq: 330, start: 0.0, dur: 0.15, type: "square", gain: 0.2, lowpass: 1200 },
      { freq: 220, start: 0.15, dur: 0.2, type: "square", gain: 0.2, lowpass: 1200 },
    ],
  },
  aiUncertain: {
    priority: 3,
    label: "AI không chắc chắn",
    help: "ba nốt lặp, rung nhẹ",
    notes: [0, 1, 2].map((i) => ({
      freq: 740, start: i * 0.14, dur: 0.08, type: "sine", gain: 0.2,
      vibrato: { rate: 6, depth: 12 },
    })),
  },
};

const durationOf = (def) => Math.max(...def.notes.map((n) => n.start + n.dur));

export class EarconPlayer {
  /**
   * @param {{ volume?: number, enabled?: boolean, audioContextFactory?: () => AudioContext }} opts
   */
  constructor({ volume = 1, enabled = true, audioContextFactory } = {}) {
    this.volume = volume;
    this.enabled = enabled;
    this._factory =
      audioContextFactory ||
      (() => {
        const AC = typeof window !== "undefined" && (window.AudioContext || window.webkitAudioContext);
        return AC ? new AC() : null;
      });
    this.ctx = null;
    this.master = null;
    this._active = null; // { name, priority, endsAt, stop }
    this._lastPlayed = {}; // name -> timestamp (ms) cho debounce
  }

  _ensureContext() {
    if (!this.ctx) {
      this.ctx = this._factory();
      if (!this.ctx) return false;
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
    }
    return true;
  }

  /** Gọi trong sự kiện phím/click đầu tiên: trình duyệt chặn âm thanh đến khi có thao tác người dùng. */
  async unlock() {
    if (!this._ensureContext()) return false;
    if (this.ctx.state === "suspended") await this.ctx.resume();
    return this.ctx.state === "running";
  }

  setVolume(v) {
    this.volume = Math.min(Math.max(v, 0), 1);
    if (this.master) this.master.gain.value = this.volume;
  }

  setEnabled(flag) {
    this.enabled = !!flag;
    if (!this.enabled) this._cancelActive();
  }

  /**
   * Phát một earcon.
   * @returns {number} thời lượng (ms) nếu được phát, 0 nếu bị bỏ qua
   */
  play(name) {
    const def = EARCON_DEFS[name];
    if (!def) throw new Error(`Earcon không tồn tại: ${name}`);
    if (!this.enabled || !this._ensureContext()) return 0;

    const nowMs = this._now();
    // Chống lặp
    if (def.debounceMs && nowMs - (this._lastPlayed[name] ?? -Infinity) < def.debounceMs) return 0;
    // Ưu tiên: âm đang phát có ưu tiên >= thì bỏ qua âm mới; thấp hơn thì bị cắt.
    if (this._active && this._active.endsAt > nowMs) {
      if (this._active.priority >= def.priority) return 0;
      this._cancelActive();
    }

    const t0 = this.ctx.currentTime + 0.01;
    const bus = this.ctx.createGain(); // bus riêng để cắt được cả earcon
    bus.connect(this.master);
    const oscillators = def.notes.map((n) => this._scheduleNote(n, t0, bus));

    const totalMs = Math.round(durationOf(def) * 1000);
    this._lastPlayed[name] = nowMs;
    this._active = {
      name,
      priority: def.priority,
      endsAt: nowMs + totalMs,
      stop: () => {
        const t = this.ctx.currentTime;
        bus.gain.cancelScheduledValues(t);
        bus.gain.setValueAtTime(bus.gain.value, t);
        bus.gain.linearRampToValueAtTime(0, t + 0.01);
        oscillators.flat().forEach((o) => { try { o.stop(t + 0.02); } catch (_) {} });
      },
    };
    return totalMs;
  }

  /**
   * Phát earcon rồi chờ xong + khoảng nghỉ trước khi gọi TTS (tránh chồng lên giọng đọc).
   * Ví dụ: await earcons.playThen("chartDetected", () => speak("Đã phát hiện một biểu đồ"));
   */
  async playThen(name, speakFn, gapMs = 120) {
    const ms = this.play(name);
    if (ms > 0) await new Promise((r) => setTimeout(r, ms + gapMs));
    return speakFn();
  }

  /** Văn bản giải thích 4 âm báo, dùng cho phím tắt trợ giúp (ví dụ phím "?") để đọc bằng TTS. */
  describe() {
    return Object.values(EARCON_DEFS)
      .map((d) => `${d.label}: ${d.help}.`)
      .join(" ");
  }

  _now() {
    return typeof performance !== "undefined" ? performance.now() : Date.now();
  }

  _cancelActive() {
    if (this._active) {
      this._active.stop();
      this._active = null;
    }
  }

  _scheduleNote(n, t0, bus) {
    const ctx = this.ctx;
    const start = t0 + n.start;
    const end = start + n.dur;
    const osc = ctx.createOscillator();
    const amp = ctx.createGain();
    osc.type = n.type || "sine";
    osc.frequency.setValueAtTime(n.freq, start);

    // Envelope để tránh tiếng "click"
    amp.gain.setValueAtTime(0.0001, start);
    amp.gain.exponentialRampToValueAtTime(n.gain, start + 0.01);
    amp.gain.exponentialRampToValueAtTime(0.0001, end);

    let head = osc;
    if (n.lowpass) {
      const f = ctx.createBiquadFilter();
      f.type = "lowpass";
      f.frequency.value = n.lowpass;
      osc.connect(f);
      head = f;
    }
    head.connect(amp);
    amp.connect(bus);

    const nodes = [osc];
    if (n.vibrato) {
      const lfo = ctx.createOscillator();
      const depth = ctx.createGain();
      lfo.frequency.value = n.vibrato.rate;
      depth.gain.value = n.vibrato.depth;
      lfo.connect(depth);
      depth.connect(osc.frequency);
      lfo.start(start);
      lfo.stop(end + 0.02);
      nodes.push(lfo);
    }
    osc.start(start);
    osc.stop(end + 0.02);
    return nodes;
  }
}

/** Instance dùng chung cho toàn ứng dụng. */
export const earcons = new EarconPlayer();
