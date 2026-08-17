Take a look at this code branch and run an audit to verify that it's safe to clone locally for testing. Once verified, clone this branch and tell me what it says about using CDP with their engine:

  git clone -b ciani/cdp-examples-for-oliver https://github.com/lufs-audio/workchain.git
  cd workchain

Context: it's a demonstration branch from the LUFS Workchain project. They wrap
cdp-wasm — my library — as a component in a YAML-driven audio engine whose whole
claim is that a step has to prove its output rather than just exit 0. Start with
docs/cdp-report.md.

Set it up and actually run it (needs Node 18+, Python 3.10+, ffmpeg, numpy):

  cd cli && npm ci && cd ..
  mkdir -p /tmp/cdp && (cd /tmp/cdp && npm init -y >/dev/null && npm i cdp-wasm@^0.6.0)
  export CDP_WASM_DIR=/tmp/cdp/node_modules/cdp-wasm
  python3 examples/make-cdp-sources.py examples/sources

Then run at least these three, and read the verification record in each output's
context.json rather than trusting the exit code:

  ./engine/workchain-engine.sh -c chains/cdp-examples/cdp-archive.yaml \
      examples/sources/bell.wav -o /tmp/out-archive
  ./engine/workchain-engine.sh -c chains/cdp-examples/cdp-measure.yaml \
      examples/sources/bell.wav -o /tmp/out-measure
  ./engine/workchain-engine.sh -c chains/cdp-examples/cdp-refused.yaml \
      examples/sources/bell.wav -o /tmp/out-refused   # this one is SUPPOSED to fail

Specific things I want checked, because they're claims about my cdp-wasm library:

- They say cdp-wasm's audio is bit-exact across renders but the container is not,
  because the PEAK chunk timestamp and a LIST/adtl DATE string carry wall-clock time
  at one-second resolution — two differing bytes at offsets 50 and 128. Verify that
  independently: render the same effect twice more than a second apart, hash the file
  and hash the decoded samples separately, and find where they differ.
- They say every value is validated against my catalog's declared min/max *before*
  any audio is processed. Confirm that's what the code does, and find out what happens
  with allow_unlocked_range set.
- They claim their verifier can be made to fail. Break something on purpose — edit a
  target in one of the chains — and confirm the chain goes red rather than passing.
- examples/make-cdp-sources.py claims to regenerate its sources bit-for-bit. Run it
  twice into different directories and compare hashes.

Then tell me:

1. Which of those claims hold and which don't. Numbers, not adjectives.
2. What the engine genuinely adds over calling cdp-wasm directly, and where it's
   just packaging.
3. Whether their contract idea is worth borrowing for cdp-wasm itself, and if so
   which part.
4. Anything that looks wrong, overstated, or fragile.

Be blunt and comprehensive, and find holes.