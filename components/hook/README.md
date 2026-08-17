# hook

Pre-renders the two artifacts that make a large collection auditionable: a short clip taken from
the **loudest window** of the file, and a waveform PNG.

Past a few thousand files, filenames stop being a way to find anything. You audition. This is
what makes that fast — you hear the part of the file that is actually doing something, not the
first three seconds of room tone.

## Params

- `hook_seconds` (default `3`) — clip length

## Contract

- `hook_clip` — exists, non-empty, and decodes as real audio
- `waveform` — exists and is non-empty

## Output

`<output>/archive/<name>.hook.wav` and `<name>.waveform.png`
