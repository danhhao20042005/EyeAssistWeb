export type EarconName =
  | 'ready'
  | 'done'
  | 'processing'
  | 'heading'
  | 'paragraph'
  | 'figure'
  | 'table'
  | 'uncertain'
  | 'low'
  | 'error';

type Tone = {
  freq: number;
  start: number;
  dur: number;
  type?: OscillatorType;
  gain?: number;
  glideTo?: number;
};

const PATTERNS: Record<Exclude<EarconName, 'processing'>, Tone[]> = {
  ready: [
    { freq: 523.25, start: 0, dur: 0.12 },
    { freq: 783.99, start: 0.12, dur: 0.18 },
  ],
  done: [
    { freq: 880, start: 0, dur: 0.14 },
    { freq: 1318.5, start: 0.1, dur: 0.22 },
  ],
  heading: [{ freq: 330, start: 0, dur: 0.1, type: 'triangle', gain: 0.9 }],
  paragraph: [{ freq: 440, start: 0, dur: 0.05, gain: 0.45 }],
  figure: [
    { freq: 784, start: 0, dur: 0.08, type: 'triangle' },
    { freq: 1174.7, start: 0.07, dur: 0.08, type: 'triangle' },
    { freq: 1568, start: 0.14, dur: 0.12, type: 'triangle' },
  ],
  table: [
    { freq: 392, start: 0, dur: 0.06, type: 'square', gain: 0.35 },
    { freq: 392, start: 0.1, dur: 0.06, type: 'square', gain: 0.35 },
    { freq: 523.25, start: 0.2, dur: 0.07, type: 'square', gain: 0.35 },
  ],
  uncertain: [
    { freq: 659.25, start: 0, dur: 0.16 },
    { freq: 440, start: 0.18, dur: 0.24 },
  ],
  low: [
    { freq: 659.25, start: 0, dur: 0.14 },
    { freq: 523.25, start: 0.16, dur: 0.14 },
    { freq: 392, start: 0.32, dur: 0.26 },
  ],
  error: [{ freq: 196, start: 0, dur: 0.32, type: 'sawtooth', gain: 0.4, glideTo: 140 }],
};

export const EARCON_LABEL: Partial<Record<EarconName, string>> = {
  ready: 'Sẵn sàng',
  done: 'Hoàn tất',
  heading: 'Tiêu đề',
  figure: 'Hình',
  table: 'Bảng',
  uncertain: 'Chưa chắc chắn',
  low: 'Không đủ tin cậy',
  error: 'Lỗi',
};

const PROCESSING_INTERVAL_MS = 700;
const PEAK_GAIN = 0.35;

type AudioWindow = Window & { webkitAudioContext?: typeof AudioContext };

class EarconPlayer {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private volume = 0.6;
  private timer: ReturnType<typeof setInterval> | null = null;

  setVolume(value: number) {
    this.volume = Math.min(1, Math.max(0, value));
    if (this.master) this.master.gain.value = this.volume;
  }

  private ensure(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    const Ctor = window.AudioContext ?? (window as AudioWindow).webkitAudioContext;
    if (!Ctor) return null;
    if (!this.ctx) {
      this.ctx = new Ctor();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') void this.ctx.resume();
    return this.ctx;
  }

  private schedule(ctx: AudioContext, tones: Tone[]) {
    const origin = ctx.currentTime + 0.01;
    for (const tone of tones) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const start = origin + tone.start;
      const end = start + tone.dur;
      const peak = PEAK_GAIN * (tone.gain ?? 1);
      osc.type = tone.type ?? 'sine';
      osc.frequency.setValueAtTime(tone.freq, start);
      if (tone.glideTo) osc.frequency.linearRampToValueAtTime(tone.glideTo, end);
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.linearRampToValueAtTime(peak, start + Math.min(0.012, tone.dur / 3));
      gain.gain.exponentialRampToValueAtTime(0.0001, end);
      osc.connect(gain);
      gain.connect(this.master ?? ctx.destination);
      osc.start(start);
      osc.stop(end + 0.02);
    }
  }

  play(name: EarconName) {
    if (name === 'processing') {
      this.startProcessing();
      return;
    }
    const ctx = this.ensure();
    if (!ctx) return;
    this.schedule(ctx, PATTERNS[name]);
  }

  startProcessing() {
    if (this.timer) return;
    const tick = () => {
      const ctx = this.ensure();
      if (ctx) this.schedule(ctx, [{ freq: 600, start: 0, dur: 0.04, gain: 0.5 }]);
    };
    tick();
    this.timer = setInterval(tick, PROCESSING_INTERVAL_MS);
  }

  stopProcessing() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  isProcessing() {
    return this.timer !== null;
  }
}

export const earconPlayer = new EarconPlayer();
