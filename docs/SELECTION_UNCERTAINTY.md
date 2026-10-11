# Selection-function uncertainty audit

This extension reuses the committed v0.5 blind-search statistics and labelled
synthetic injections. It does not rerun or alter the light-curve fits and does
not estimate Roman mission yield, population completeness, or an operational
false-positive rate.

## Detection-threshold operating curve

For each fixed threshold `T`, a row is counted as detected only when the blind
fit succeeded and `delta_chi2 > T`. Wilson 95% intervals are reported
separately for the balanced point-lens injection grid and the Gaussian
constant-flux null. `balanced_precision` gives both classes equal prior weight;
it must not be read as an astrophysical positive predictive value because real
class prevalence and contaminants are absent.

## Cadence-dropout retention

If a trial originally has `n` epochs within one injected Einstein time and
each epoch is independently retained with probability `1-f`, the probability
of retaining at least `m=3` epochs is

`P(K >= m) = 1 - sum_{k=0}^{m-1} Binomial(k | n, 1-f)`.

This isolates cadence-support loss. It does not model correlated outages,
photometric refitting, detector systematics, or event detection after gaps.

## Injection-count planning

The smallest per-bin sample whose Wilson half-width reaches 10%, 5%, 3%, or
2% is calculated for assumed recovery fractions 0.1, 0.5, and 0.9. The 0.5
case is the conservative binomial planning case. These counts address
statistical precision only; they do not fix model misspecification or coverage
of the physical parameter space.

## Reproduce

```bash
python scripts/analyze_selection_uncertainty.py
pytest -q tests/test_selection_uncertainty.py
```

All generated CSV/JSON/PNG outputs retain the synthetic-experiment scope.
