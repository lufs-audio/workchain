# cdp-wasm inside a verifying engine — what we found

**For Oliver Larkin · 17 August 2026 · LUFS Audio**

This is the text form of `docs/cdp-report.html`, for reading rather than looking at. The HTML
version carries the audio and the spectrograms; this one carries the numbers.

Everything here was executed against **cdp-wasm 0.6.0**. Every duration, frame count and distance
is read out of a run artifact — a `context.json` or a component record. Sources are synthesised
rather than sampled, and `examples/make-cdp-sources.py` regenerates them bit-for-bit.

The set is graded: it starts with CDP doing what CDP does, then adds one layer at a time. Each
section says what is gained, including the first, where the answer is nothing.

---

## Act I — CDP, just running

A chain is YAML. A step names an effect and its values; the engine resolves parameters, runs the
render, and passes the result on. At this level Workchain is a runner and nothing more.

| chain | effect | source | result |
| --- | --- | --- | --- |
| `chains/cdp-examples/cdp-bloom.yaml` | `stretch.time` factor 8 | shaker 0.45s | **3.805s** — transient becomes envelope, noise becomes pitch |
| `chains/cdp-examples/cdp-wash.yaml` | `stretch.time` factor 6 | bell 1.6s | **9.749s** — strike smeared across the whole duration |
| `chains/cdp-examples/cdp-dissolve.yaml` | `blur.blur`, windows 1→80 via breakpoint envelope | pluck 1.8s | dissolves across its own decay |
| `chains/cdp-examples/cdp-trace.yaml` | `hilite.trace` partials 6 | bell 1.6s | inharmonic character survives, noise floor does not |
| `chains/cdp-examples/cdp-widen.yaml` | `stretch.spectrum` divide 400 stretch 3 | shaker | frequency axis only; duration preserved |

**Gained: nothing.** This is CDP with a nicer front door. Any of these is four lines of
JavaScript against the cdp-wasm API.

---

## Act II — a step that cannot report success without evidence

Every component declares a contract, and one verifier re-measures the artifact after the run.
For the CDP wrapper that is **eleven checks**: the output exists, decodes, and carries real audio
above a liveness floor; every supplied value was inside the catalog's declared range; any
breakpoint envelope was actually staged and applied rather than silently ignored; and the render
is reproducible. A step passes only when all of them hold.

The envelope check is the one that matters most. A knob that accepts a curve and quietly ignores
it is worse than a knob that is absent, because you cannot hear the difference between a subtle
envelope and no envelope.

### Two layers, independently, on the case you fixed

`chains/cdp-examples/cdp-refused.yaml` drives `stretch.time` to `0.02` — the zero-frame case from
issue #4. The wrapper validates against the catalog **before any audio is touched**:

```
cdp_transform: refusing to process: 1 out-of-range and 0 unknown parameter(s) for 'stretch.time':
    factor=0.02 — outside the catalog curated range (0.25..8)
```

Bypass the wrapper and call `applyEffect` directly, and **0.6.0 catches it itself**:

```
threw — stretch.time produced a WAV with no audio frames. CDP can write an empty output
without reporting an error when a parameter is far outside its declared range — check the
values against the catalog's min/max.
```

Neither layer needs the other, which is the right arrangement.

On the design question in the issue: **the output guard was the right call over range
validation**, and I only half saw it when I filed. Re-running the whole threshold table against
0.6.0:

```
factor  0.03 → 1280 frames   0.04 → 1664   0.05 → 2176   0.10 → 4352
        0.25 → 11136 (declared min)      2 → 90240
```

Every value below the declared minimum of 0.25 still produces audio, with frame counts identical
to 0.5.3. Validating against the curated range would have rejected all of them.

**Gained: a step that cannot lie about its own output** — and, for an agent driving the tool
unattended, a failure that arrives as a refusal rather than a silent file nobody listens to.

---

## Act III — transforms become comparable to each other

`chains/cdp-examples/cdp-measure.yaml` is the pattern: `cdp_transform → features → embed`.
Eleven effects on the same struck bar, each result measured twice — deterministic DSP features,
and a 64-dimension L2-normalised embedding. Because the contract guarantees
the norm, cosine distance is meaningful, so "how far did this effect move the sound" becomes a
number you can sort by.

| effect | what it does | distance (1 − cos) | Δ centroid Hz |
| --- | --- | --- | --- |
| `blur.scatter` | keep only 2 of every 32 windows | 0.9561 | -921 |
| `blur.suppress` | remove the 12 loudest partials | 0.5986 | +2276 |
| `blur.chorus` | randomise amplitude and frequency per partial | 0.3800 | +1112 |
| `strange.waver` | vibrato applied in the frequency domain | 0.1976 | +1066 |
| `focus.accu` | accumulate spectrum with an upward glissando | 0.1589 | +872 |
| `strange.invert` | invert the spectrum | 0.0612 | +727 |
| `stretch.spectrum` | pull partials apart above 800 Hz | 0.0599 | +376 |
| `hilite.trace` | keep only the 4 loudest partials | 0.0438 | -649 |
| `focus.exag` | exaggerate spectral contrast | 0.0244 | +1370 |
| `blur.blur` | smear 40 analysis windows together | 0.0206 | +147 |
| `hilite.pluck` | emphasise onsets | 0.0000 | +10 |

Baseline: centroid **1258.06 Hz**, brightness
**0.1141**, rms **-12.66 dBFS**.

The two measurements corroborate each other, which is the only reason either is worth reporting.
`blur.suppress` removes the twelve loudest partials, so the centroid climbs **+2276 Hz** — what
remains is what was quiet and high. `hilite.pluck` emphasises onsets, and a struck bar's onset
already dominates, so it barely moves the sound at all: distance **0.0000**, centroid **+10 Hz**.

**Gained: a catalog navigable by intent.** An agent asked for "something that keeps the identity
of this sound" picks from the bottom of that list; one asked to destroy it picks from the top —
without a human having auditioned 232 effects first.

> The embedding is `melstats-v0`, a dependency-light numpy log-mel band-energy vector standing in
> for LAION-CLAP behind the same vector contract. The distances are real. They are not CLAP
> distances.

---

## Act IV — past the edge of CDP

`chains/cdp-examples/cdp-archive.yaml` — one chain, five steps, **30 checks**:

```
cdp_transform → probe → features → embed → hook
```

The transform is one step of five; the other four have no CDP equivalent. They are what turns a
file in a folder into an entry in a library.

| step | produces |
| --- | --- |
| `probe` | content SHA-256 `91c779b0ccc952bf…`, identifier `lufs-91c779b0`, duration 1.6225s, peak -8.8 dBFS, and which decoder read it |
| `features` | centroid 3533.61 Hz · rolloff85 4345.67 Hz · rms -35.35 dBFS · zcr 0.35041 · brightness 0.3205 |
| `embed` | `melstats-v0`, dim 64, L2 norm 1.0 |
| `hook` | a 3s clip cut from the **loudest window**, plus a waveform PNG |

Past a few thousand files, filenames stop being a way to find anything and auditioning becomes
the only interface that works.

**Gained: the render stops being a dead end.** It has an identity, a measured description, a
position in a vector space, and something you can hear in three seconds — so the next question can
be "find me the others like this" rather than "what did I call that file".

---

## Two smaller notes

**`grain.reverse` gave no output on any source tried.** Four synthetic sources — 1.0s and 3.0s at
233 Hz, 1.0s at 80 Hz, 0.5s at 440 Hz — each returned `grain produced no output (exit -1)` with an
`ERROR: INVAL` underneath. Probably not a defect: the grain programs segment on amplitude troughs
and a smooth decaying sine has no grain onsets, so zero grains may be exactly correct. Raised only
because the message does not say that.

**`hardMin` / `hardMax` are declared by one effect of 232.** We expose an "unlock the range" switch
that falls back to engine hard limits where the catalog records them, and in practice only
`rotor.rotor` does — so for everything else the curated range stays the effective limit even when
unlocked. A data-coverage observation rather than a bug.

---

## Curious on where you think a contract belongs

You put the guard at the output because the curated range is meant to be leaveable. That is a
judgement about where truth is cheapest to establish, and it is the same judgement every component
in this engine has to make. How would you draw that line across 232 programs rather than one?

Two other things I would enjoy comparing notes on. Your `cdp-sound-design` patch format
distinguishes `linear`, `two-input` and `graph`; we arrived at the same three categories from the
other direction and are currently linear-only, with two-input next — converging independently on
the same taxonomy suggests it is the real shape of the problem. And on similarity and tagging:
Act III is a placeholder behind a fixed contract, and the interesting version swaps it for CLAP
over a large personal archive.

---

Engine and CLI: <https://github.com/lufs-audio/workchain> · Apache-2.0 · `npm i -g @lufs-audio/workchain`

Thank you for the fast fix on #4. — Daniel Ramirez, LUFS Audio
