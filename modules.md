# Audit modules

These are conditional checks, not automatic error detectors. Establish definitions and assumptions first.

## A Main and supplement consistency

- Inventory references to sections, tables, figures, algorithms, equations, assumptions and theorems. Resolve both directions; expand ranges and handle prefixes, letters, plurals and aliases. Regex only generates candidates. Unreferenced supplement objects are not automatically errors.
- Compare theorem statements with actual proof and lemma assumptions. Check global assumptions before declaring a condition missing.
- Reconcile shared cells, figure captions, identifiers, ordering, counts and signs. Check missing/duplicate panels visually.
- Reconcile citations and bibliography scope; separate bibliographies may be intentional.
- Compare cohort/covariate descriptions, estimands, tuning, seeds and replication counts only after matching experiments/populations.

## B Numerical verification

Save reproduction code/output. Use printed precision and rounding intervals, not arbitrary exact equality.

- Reconcile totals, percentages and weighted means for compatible denominators, populations, units and missing-data rules. Example: 1/3 printed as 33.3% is consistent to one decimal.
- SE = sqrt(p(1-p)/R) requires independent Bernoulli replicates and Monte Carlo SE of a proportion. Check SE vs SD, bootstrap SE, CI half-width and percent units. Prefer stated R. Inferred R is exploratory: handle rounding, boundary p, dependence, unequal R and no eligible cells. Fixed-tolerance flags are not confirmed errors.
- Empirical slopes are diagnostics. Distinguish theoretical upper bounds from exact rates and limits, and variance from RMSE, squared error, interval length and bias. A few finite-sample points cannot establish or refute asymptotic rates.
- Recompute statistics under the stated parameterization. Compare p-value ranks only after checking tail direction and common calibration. Different degrees of freedom, standard errors, nuisance estimates, two-sided transformations and multiplicity adjustments can change ordering. Grid-search fits do not establish which parameter authors used.
- Independently derive true parameter values. Simulation means are evidence, not ground truth; investigate bias, implementation, parameterization and labels.
- Check transformations, totals, intervals and p-values conditional on actual methods. Bootstrap, one-sided or bias-corrected intervals need not obey Wald-interval expectations.

## C Journal structure optional

Obtain dated official instructions or user-supplied policy for the requested journal. Upstream ACS examples (>25% real-data pages and roughly one simulation-summary page) are not verified current requirements; do not enforce them without a source.

Map scientific questions to results. Describe allocation of real-data analysis, simulations, diagnostics, sensitivity, baselines, uncertainty and reproducibility. Mechanical presence differs from scientific adequacy. Separate recommendations from factual violations; unavailable policy is inconclusive.

## D Proof checking

Build an assumptions -> lemmas -> key steps -> conclusion map per theorem. Track quantifiers, exact/probabilistic statements and regimes of limits.

- Reconcile hypotheses, dependence, uniformity, domains and implicit constants. Test boundaries allowed by the statement, not cases violating its assumptions.
- Re-derive substituted bounds, identities, signs, indices, dimensions and normalizations. Pseudoinverse/whitening claims require original covariance and the appropriate subspace.
- Check existence for the actual estimator/distribution. Distinguish likelihood from negative log likelihood, separation from generic nonexistence, identifiability from uniqueness and local from global optimization.
- Separate misspecification, fixed approximation error and shrinking approximation error before asserting drift or divergent bias.
- Efficiency needs the model, tangent-space closure/inner product, valid scores and influence-function/projection argument. Support equality alone does not establish or refute efficiency.
- Comparing upper bounds does not prove ordering of actual risks; distinguish bound, risk and rate improvement claims.
- Verify MM/coordinate surrogate conditions and exactness. Gradient steps can descend with suitable smoothness/step sizes; missing step-size conditions may be a gap rather than demonstrated increase.
- Compare cited external results against exact statements/hypotheses; unavailable sources remain unresolved.

Numerical counterexamples must implement the printed claim, satisfy assumptions and control numerical error. Simulation support is not proof. Error requires a contradiction/counterexample; Gap identifies an unsupported implication or missing hypothesis; Defect is typographic. Keep uncertain diagnoses inconclusive.
