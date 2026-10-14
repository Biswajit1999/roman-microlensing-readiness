# Finite-source linear limb darkening — research extension

The new `romanmlr.limb_darkening` module implements **three separate numerical diagnostics**:

1. Disk-averaged point-lens magnification under the linear limb law, varying the coefficient and impact parameter.
2. Finite-exposure integration along a rectilinear point-lens trajectory (top-hat exposure, Gaussian quadrature in time).
3. Radial/angular quadrature-order convergence diagnostics, including points near the source radius.

Intensity is `I(mu)/I(1)=1-c(1-mu)`, with `mu=sqrt(1-r^2/rho^2)` and total unlensed flux normalization `1-c/3`. The finite-source calculation is numerical and does not depend on a claimed closed-form limb-darkened magnification. `c=0` is the uniform-disk limit. A centrally aligned lens preferentially magnifies the brighter disk centre, raising the peak for positive `c`. A long exposure can smear a sharp peak.

Run `python scripts/analyze_limb_darkening.py --out results/limb_darkening_pilot` after `pip install -e .`. All outputs are synthetic, not Roman flight data or yield predictions. The direct polar quadrature can converge slowly when the lens crosses an integration node or the source boundary; compare orders and avoid claiming sub-per-mille precision without independent adaptive/analytic validation. This module is additive and does **not** silently replace the uniform-disk baseline in the existing detection pipeline. It addresses the physics behind issue #2, but integration into the main FSPL API and recovery pipeline remains future work.
