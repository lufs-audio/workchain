#!/usr/bin/env python3
"""Generate the three source sounds the CDP example chains are written against.

Deterministic — seeded RNG and closed-form synthesis, so two people on two machines get
byte-identical files. That is deliberate: a committed binary fixture is one nobody can
regenerate, and an example whose input you cannot reproduce is an example you cannot check.

    python3 examples/make-cdp-sources.py [outdir]     # default: ./examples/sources

Requires numpy. Writes 16-bit mono WAV at 44.1 kHz via the standard library.
"""
import sys, wave, pathlib
import numpy as np

SR = 44100


def write(path, x):
    x = np.clip(x, -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print("  %-12s %5.2f s  peak %.3f" % (path.name, len(x) / SR, float(np.abs(x).max())))


def bell(dur=1.6, f0=233.08):
    """Struck metal bar. Inharmonic partials over a fast noise transient — the canonical
    source for spectral stretching, because there is a lot to smear."""
    t = np.arange(int(SR * dur)) / SR
    partials = [(1.00, 1.00, 2.6), (2.76, 0.62, 2.1), (5.40, 0.41, 1.7),
                (8.93, 0.28, 1.35), (13.34, 0.17, 1.05), (18.64, 0.11, 0.8)]
    x = np.zeros_like(t)
    for mult, amp, decay in partials:
        jitter = 1 + 0.0012 * np.sin(2 * np.pi * 0.7 * t + mult)   # slight beating, keeps it alive
        x += amp * np.exp(-t / decay) * np.sin(2 * np.pi * f0 * mult * jitter * t)
    strike = np.exp(-t / 0.004) * np.random.default_rng(7).normal(0, 0.5, len(t))
    x = x + strike * np.exp(-t / 0.02)
    x *= np.minimum(1, t / 0.0008)                                  # de-click the attack
    return x / np.abs(x).max() * 0.89


def shaker(dur=0.45, fc=4200.0, q=3.0):
    """Short filtered noise burst. Almost nothing to work with, which is what makes an
    eightfold stretch of it surprising."""
    t = np.arange(int(SR * dur)) / SR
    n = np.random.default_rng(19).normal(0, 1, len(t))
    w0 = 2 * np.pi * fc / SR
    alpha = np.sin(w0) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha                                 # biquad bandpass
    a0, a1, a2 = 1 + alpha, -2 * np.cos(w0), 1 - alpha
    y = np.zeros_like(n)
    x1 = x2 = y1 = y2 = 0.0
    for i, xv in enumerate(n):
        yv = (b0 * xv + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0
        y[i] = yv
        x2, x1 = x1, xv
        y2, y1 = y1, yv
    y *= np.exp(-t / 0.09) * np.minimum(1, t / 0.002)
    return y / np.abs(y).max() * 0.85


def pluck(dur=1.8, f0=146.83, shaker_dur=0.45):
    """Plucked string. Harmonic, so it contrasts with the bell under the same blur.

    The per-harmonic phases come from generator 19 *after* it has produced the shaker's
    noise, because that is the order the original run drew them in and the rendered
    examples in docs/cdp-report.html were made from those exact samples. Reproduced
    faithfully rather than tidied, so the committed chains and the report agree
    bit-for-bit; drawing from a fresh generator gives a different — equally valid, but
    different — instrument.
    """
    t = np.arange(int(SR * dur)) / SR
    rng = np.random.default_rng(19)
    rng.normal(0, 1, int(SR * shaker_dur))          # consumed by shaker() in the original run
    x = np.zeros_like(t)
    for h in range(1, 26):
        x += (1.0 / h ** 1.35) * np.exp(-t / (1.9 / h ** 0.5)) * \
             np.sin(2 * np.pi * f0 * h * t + rng.uniform(0, 2 * np.pi))
    x *= np.minimum(1, t / 0.0015)
    return x / np.abs(x).max() * 0.87


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "examples/sources")
    out.mkdir(parents=True, exist_ok=True)
    print("writing to %s/" % out)
    write(out / "bell.wav", bell())
    write(out / "shaker.wav", shaker())
    write(out / "pluck.wav", pluck())


if __name__ == "__main__":
    main()
