/**
 * Novaboard — Zero-Latency Mechanical Sound Engine (Web Audio API)
 * Synthesizes tactile mechanical switch clicks, relay ticks, dry confirmation thuds,
 * and low-frequency error pulses in real time without external .mp3/.wav files.
 */

export class MechanicalSoundEngine {
  private ctx: AudioContext | null = null;
  private enabled: boolean = true;

  constructor(initialEnabled: boolean = true) {
    this.enabled = initialEnabled;
  }

  private getContext(): AudioContext | null {
    if (!this.enabled || typeof window === "undefined") return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public setEnabled(state: boolean): void {
    this.enabled = state;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public toggle(): boolean {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.playConfirmClick();
    }
    return this.enabled;
  }

  /**
   * Stream / Typing / Selection Relay Tick (150Hz - 380Hz short mechanical impulse)
   */
  public playStreamTick(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    const filter = ctx.createBiquadFilter();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(320, now);
    osc.frequency.exponentialRampToValueAtTime(155, now + 0.018);

    filter.type = "bandpass";
    filter.frequency.setValueAtTime(260, now);
    filter.Q.setValueAtTime(1.8, now);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.075, now + 0.002);
    gain.gain.exponentialRampToValueAtTime(0.0008, now + 0.018);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.02);
  }

  /**
   * Confirmation / Completion Switch Thud (Physical mechanical key bottom-out click/thud)
   */
  public playConfirmClick(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    // 1. Low mechanical body thud (190Hz -> 85Hz)
    const bodyOsc = ctx.createOscillator();
    const bodyGain = ctx.createGain();
    bodyOsc.type = "sine";
    bodyOsc.frequency.setValueAtTime(190, now);
    bodyOsc.frequency.exponentialRampToValueAtTime(85, now + 0.038);

    bodyGain.gain.setValueAtTime(0.001, now);
    bodyGain.gain.linearRampToValueAtTime(0.14, now + 0.002);
    bodyGain.gain.exponentialRampToValueAtTime(0.001, now + 0.042);

    bodyOsc.connect(bodyGain);
    bodyGain.connect(ctx.destination);
    bodyOsc.start(now);
    bodyOsc.stop(now + 0.045);

    // 2. Crisp switch leaf contact transient (380Hz -> 210Hz)
    const clickOsc = ctx.createOscillator();
    const clickGain = ctx.createGain();
    clickOsc.type = "triangle";
    clickOsc.frequency.setValueAtTime(380, now + 0.012);
    clickOsc.frequency.exponentialRampToValueAtTime(210, now + 0.032);

    clickGain.gain.setValueAtTime(0.001, now + 0.012);
    clickGain.gain.linearRampToValueAtTime(0.09, now + 0.014);
    clickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.034);

    clickOsc.connect(clickGain);
    clickGain.connect(ctx.destination);
    clickOsc.start(now + 0.012);
    clickOsc.stop(now + 0.036);
  }

  /**
   * Error / Warning Mechanical Low-Frequency Pulse
   */
  public playErrorTone(): void {
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    for (const offset of [0, 0.055]) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(145, now + offset);
      osc.frequency.exponentialRampToValueAtTime(105, now + offset + 0.04);

      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(340, now + offset);

      gain.gain.setValueAtTime(0.001, now + offset);
      gain.gain.linearRampToValueAtTime(0.11, now + offset + 0.003);
      gain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.042);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + offset);
      osc.stop(now + offset + 0.045);
    }
  }
}

export const soundEngine = new MechanicalSoundEngine(true);
