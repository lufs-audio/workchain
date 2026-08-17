# LUFS Workchain — CDP examples

> **This is a demonstration branch, not a merge candidate.** It exists to answer one question:
> what does a verifying engine add to [cdp-wasm](https://github.com/cdp-wasm-suite/cdp-wasm)?
>
> The canonical engine lives on [`main`](https://github.com/lufs-audio/workchain/tree/main) —
> start there for anything other than this. The branch adds four components, eight example
> chains, and a report.

**Start with [`docs/cdp-report.md`](docs/cdp-report.md).** It is the findings in text. There is a
richer version at [`docs/cdp-report.html`](docs/cdp-report.html) with the audio and the
spectrograms embedded — GitHub will not render it in the browser, so download it and open it
locally.

---

## What Workchain is

A YAML-driven, agent-first audio processing engine whose defining promise is **verifiable
correctness**: *"works" means proven correct, not merely exited 0.*

Self-contained **components** (a `step.yaml` contract + a `run.sh` + a README) compose into
declarative **chains**. Every component declares what must be true of its output, and a single
verifier re-measures the artifact after the run — so a step passes only when the file exists,
decodes, carries the declared keys, and satisfies its numeric post-conditions. Three interfaces
(a Bash engine, a Node CLI, a Python MCP server) share one parser so they cannot silently diverge.

`cdp_transform` wraps cdp-wasm's 232 effects under a fail-closed parameter and output contract.
It is the one component in the project that wraps someone else's library, which is why it is the
interesting one.

## Run it

Requires **Node 18+**, **Python 3.10+**, **ffmpeg** (with `ffprobe`), and `numpy`.

```bash
git clone -b ciani/cdp-examples-for-oliver https://github.com/lufs-audio/workchain.git
cd workchain
cd cli && npm ci && cd ..

# cdp-wasm is an optional dependency; install it where the component can find it
mkdir -p /tmp/cdp && (cd /tmp/cdp && npm init -y >/dev/null && npm i cdp-wasm@^0.6.0)
export CDP_WASM_DIR=/tmp/cdp/node_modules/cdp-wasm

# generate the three source sounds (deterministic — regenerates bit-for-bit)
python3 examples/make-cdp-sources.py examples/sources

# a transform
./engine/workchain-engine.sh -c chains/cdp-examples/cdp-bloom.yaml \
  examples/sources/shaker.wav -o /tmp/out-bloom

# the interesting one: transform, then everything CDP has no equivalent for
./engine/workchain-engine.sh -c chains/cdp-examples/cdp-archive.yaml \
  examples/sources/bell.wav -o /tmp/out-archive

# and the one that must FAIL — an out-of-range parameter, refused before any audio is touched
./engine/workchain-engine.sh -c chains/cdp-examples/cdp-refused.yaml \
  examples/sources/bell.wav -o /tmp/out-refused ; echo "exit $?"
```

The verification record is the point. After any run:

```bash
python3 -c "
import json,sys
c=json.load(open(sys.argv[1]))
for name,s in c['steps'].items():
    v=s.get('verification') or {}
    print(f\"{name:<18} verified={v.get('verified')} checks={len(v.get('checks') or [])}\")
    for ch in v.get('checks') or []: print('   ', ch.get('name'), '—', ch.get('detail'))
" /tmp/out-archive/context.json
```

## The chains

| chain | what it shows |
| --- | --- |
| `cdp-bloom.yaml` | `stretch.time` ×8 — a 0.45s shaker becomes 3.8s |
| `cdp-wash.yaml` | `stretch.time` ×6 — a struck bar held open for ~10s |
| `cdp-dissolve.yaml` | `blur.blur` with `windows` driven **1 → 80 by a breakpoint envelope** |
| `cdp-trace.yaml` | `hilite.trace` — keep the 6 loudest partials per window |
| `cdp-widen.yaml` | `stretch.spectrum` — the frequency axis, duration preserved |
| `cdp-measure.yaml` | transform → `features` → `embed`: the result measured two independent ways |
| `cdp-archive.yaml` | transform → `probe` → `features` → `embed` → `hook`: **30 checks over 5 steps** |
| `cdp-refused.yaml` | an out-of-range parameter. **This one is supposed to fail** |

## The components on this branch

Beyond `main`'s set, four light components with no CDP equivalent — numpy, ffmpeg and the standard
library only, no models and no venv:

| component | what it does |
| --- | --- |
| [`probe`](components/probe) | content SHA-256, container and stream facts, measured level. A probe it cannot measure **fails** rather than writing nulls |
| [`features`](components/features) | spectral centroid, 85% rolloff, RMS, zero-crossing rate, brightness. `bpm`/`key` are declared **null** rather than estimated badly |
| [`embed`](components/embed) | an L2-normalised float32 vector behind a **stable contract** — swap the model, keep the interface |
| [`hook`](components/hook) | a clip cut from the loudest window plus a waveform PNG, so a large collection is auditionable |

These are ported copies: their in-repo documentation was rewritten for this branch to drop
references to the private pipeline they were originally built for. The code is unchanged.

## A note for whoever checks this out

Two things worth knowing, because they are the kind of thing this project exists to surface.

**The examples are reproducible on purpose.** `examples/make-cdp-sources.py` regenerates the three
sources bit-for-bit rather than committing WAVs, because a committed binary fixture is one nobody
can regenerate. The pluck's phase seeding looks odd and is commented — it faithfully reproduces
the draw order of the original run, so the chains and the report agree exactly.

**cdp-wasm's audio is bit-exact run to run.** Its *container* is not: the `PEAK` chunk timestamp
and a `LIST/adtl` `DATE` string both carry wall-clock time at one-second resolution, so two
identical renders differ in exactly two bytes when they straddle a second boundary. That matters
if you content-address the output — as `probe` does. `cdp_transform` therefore compares decoded
samples, not files, and records the container comparison separately as a non-gating fact.

---

Apache-2.0 · `npm i -g @lufs-audio/workchain` · [lufs.audio](https://lufs.audio)
