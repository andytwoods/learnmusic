class PitchProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const o = (options && options.processorOptions) || {};
    this.fs    = o.sampleRate || 48000;
    this.N     = o.windowSize || 4096;
    this.hop   = o.hopSize || 240;
    this.buf   = new Float32Array(this.N * 2);
    this.wpos  = 0;
    this.frame = 0;
    this.hpLast = 0;
  }
  hpf(x) {
    const RC = 1/(2*Math.PI*60);
    const dt = 1/this.fs;
    const alpha = RC/(RC+dt);
    const y = alpha*(this.hpLast + x - (this.prevIn || 0));
    this.prevIn = x; this.hpLast = y; return y;
  }
  process(inputs) {
    const ch = inputs[0];
    if (!ch || ch.length===0) return true;
    const x = ch[0];
    for (let i=0;i<x.length;i++) {
      const s = this.hpf(x[i]);
      this.buf[this.wpos] = s;
      this.wpos = (this.wpos + 1) % this.buf.length;
      this.frame++;
      if (this.frame % this.hop === 0) {
        const slice = this.latest(this.N);
        const rms = this.computeRMS(slice);
        let hz=0, conf=0;
        if (rms > 0.005) {
          const { freq, clarity } = this.mpm(slice, this.fs);
          hz = freq || 0;
          conf = clarity || 0;
        }
        this.port.postMessage({ hz, conf, rms: this.dbfs(rms), t: currentTime });
      }
    }
    return true;
  }
  latest(n) {
    const out = new Float32Array(n);
    const start = (this.wpos - n + this.buf.length) % this.buf.length;
    for (let i=0;i<n;i++) out[i] = this.buf[(start+i) % this.buf.length];
    return out;
  }
  computeRMS(a) { let s=0; for (let i=0;i<a.length;i++) s+=a[i]*a[i]; return Math.sqrt(s/a.length); }
  dbfs(rms){ const v = rms <= 1e-9 ? 1e-9 : rms; return 20*Math.log10(v); }
  centreClip(x, pct){
    let max = 0; for (let i=0;i<x.length;i++) max = Math.max(max, Math.abs(x[i]));
    const t = max * pct;
    const y = new Float32Array(x.length);
    for (let i=0;i<x.length;i++){ const v = x[i]; y[i] = Math.abs(v) >= t ? v : 0; }
    return y;
  }
  mpm(x, fs) {
    const N = x.length;
    const tauMax = Math.floor(fs / 50);    // ~50 Hz lowest
    const tauMin = Math.floor(fs / 1000);  // ~1 kHz highest
    const clip = this.centreClip(x, 0.2);
    const nsdf = new Float32Array(tauMax+1);
    let maxPos = -1, maxVal = -1;
    for (let tau=tauMin; tau<=tauMax; tau++) {
      let acf=0, m=0;
      for (let i=0;i<N-tau;i++) {
        const a = clip[i], b = clip[i+tau];
        acf += a*b; m += a*a + b*b;
      }
      nsdf[tau] = m>0 ? (2*acf/m) : 0;
      if (nsdf[tau] > maxVal) { maxVal = nsdf[tau]; maxPos = tau; }
    }
    let tau = maxPos;
    if (tau>0 && tau<tauMax) {
      const y1 = nsdf[tau-1], y2 = nsdf[tau], y3 = nsdf[tau+1];
      const denom = (2*(2*y2 - y1 - y3));
      if (denom !== 0) { const delta = (y1 - y3)/denom; tau = tau + delta; }
    }
    const clarity = Math.max(0, maxVal);
    const freq = tau>0 ? fs / tau : 0;
    return { freq, clarity };
  }
}

registerProcessor('pitch-worklet', PitchProcessor);
