# features

Cheap, deterministic DSP features via numpy: spectral centroid, 85% rolloff, RMS, zero-crossing
rate, and a brightness ratio. No model, no venv.

`bpm` and `key` are declared **null** in this version rather than estimated badly — a field that
reports a confident wrong answer is worse than a field that admits it has none.

**A failed decode fails the step** rather than reporting a zeroed measurement, and
`decoded_duration_s` records how much audio was actually measured, so a truncated read is
visible instead of silent.

## Contract

- `features` — exists, non-empty, valid JSON, declared keys present
- post-condition `features_measured_not_assumed` — the record must show real measurement

## Output

`<output>/archive/<name>.features.json`
