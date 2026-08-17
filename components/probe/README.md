# probe

Deterministic identity and facts for one audio file. No heavy dependencies — `ffprobe`,
`ffmpeg` and the Python standard library only.

Writes a record containing the SHA-256 of the file, a short identifier derived from it,
container and stream facts (duration, sample rate, channels, codec), and measured peak and
mean level.

**A probe it cannot measure fails.** It never writes a record with null measurements. If
`ffmpeg` refuses a WAV whose chunk table is malformed, the component salvages a readable copy
with the standard library and records *which* path was used in `decoder`, so a degraded read
can never be mistaken for a clean one.

## Contract

- `probe` — asserted to exist, be non-empty, be valid JSON, and carry the declared keys
- post-condition `probe_facts_plausible` — the recorded facts must be internally consistent

## Output

`<output>/archive/<name>.probe.json`
