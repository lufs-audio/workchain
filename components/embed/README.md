# embed

An audio embedding behind a **stable vector contract**: audio in, an L2-normalised float32
vector of declared dimension out. Because the norm is guaranteed, cosine similarity between two
records is meaningful without further work.

This version ships `melstats-v0` — a dependency-light log-mel band-energy vector computed with
numpy. It stands in for a production model (LAION-CLAP, MuQ-MuLan) **without changing the
contract**: swap the model, keep the interface, and everything downstream that consumed vectors
keeps working. The record stamps which model produced it, so a substitution can never hide.

The distances it produces are real. They are not CLAP distances.

## Contract

- `embedding` — exists, non-empty, valid JSON, declared keys present

## Output

`<output>/archive/<name>.embedding.json`
