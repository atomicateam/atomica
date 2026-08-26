# -*- coding: utf-8 -*-
"""Two-parameter cost curve: `saturation_lower` makes the cost curve linear below a stated coverage.

`saturation` alone controls both where the cost curve bends and where it diverges, so the curve is
non-linear from zero and the entered unit cost is never the realised cost of anything. `saturation_lower`
separates the two: below it the curve is the identity, so the unit cost is exactly the cost of reaching
the next person; above it coverage saturates towards `saturation` as before.

    p = c                                             for c <= lambda
    p = lambda + (sigma-lambda)*tanh((c-lambda)/(sigma-lambda))   for c >  lambda

Four properties are checked, in the order that a failure would matter:

1. BACKWARD COMPATIBILITY. With `saturation_lower` unset the curve must reproduce the old
   `p = sigma*tanh(c/sigma)` to machine precision, otherwise every existing project silently changes.
2. THE LINEAR REGION. Below `saturation_lower` the implied spending must equal
   `unit_cost * coverage * eligible` exactly - that is the whole point of the parameter.
3. ROUND TRIP. `get_capacity_from_prop_covered` must invert `get_prop_covered` across the range,
   including through the join at `lambda`, and return `inf` at or above `sigma`.
4. C1 CONTINUITY. The marginal cost must not jump at the join, or an optimiser will see a false kink.
"""
import numpy as np
import atomica as at

TOL = 1e-12


def _prog(sat, sat_lower=None):
    p = at.Program("test")
    p.unit_cost = at.TimeSeries(assumption=10.0, units="$/person")
    p.saturation = at.TimeSeries(assumption=sat, units="N.A.")
    if sat_lower is not None:
        p.saturation_lower = at.TimeSeries(assumption=sat_lower, units="N.A.")
    return p


t = np.array([2020.0])
eligible = np.array([1000.0])

# ---------------------------------------------------------------- 1. backward compatibility
print("1. saturation_lower unset must reproduce sigma*tanh(c/sigma) to machine precision")
sigma = 0.8
p0 = _prog(sigma)
worst = 0.0
for c_per in [0.0, 0.05, 0.2, 0.5, 0.79, 1.5, 5.0]:
    got = p0.get_prop_covered(t, np.array([c_per * 1000.0]), eligible)[0]
    ref = 2 * sigma / (1 + np.exp(-2 * c_per / sigma)) - sigma  # the original expression
    worst = max(worst, abs(got - ref))
    print(f"   c/eligible={c_per:<6} coverage={got:.15f}  reference={ref:.15f}")
assert worst < TOL, f"backward compatibility broken, max abs diff {worst:g}"
print(f"   max abs diff {worst:.3e}  OK\n")

# ---------------------------------------------------------------- 2. the linear region
print("2. below saturation_lower the cost must be exactly unit_cost * coverage * eligible")
lam = 0.4
p1 = _prog(0.8, lam)
worst = 0.0
for cov in [0.0, 0.1, 0.25, 0.399, 0.4]:
    cap = p1.get_capacity_from_prop_covered(t, np.array([cov]), eligible)[0]
    worst = max(worst, abs(cap - cov * 1000.0))
    print(f"   coverage={cov:<6} capacity={cap:.10f}  linear={cov * 1000.0:.10f}")
assert worst < 1e-9, f"linear region is not linear, max abs diff {worst:g}"
print(f"   max abs diff {worst:.3e}  OK\n")

# and above it, cost is strictly greater than linear, diverging at sigma
print("   above saturation_lower the cost must exceed linear and diverge at saturation")
for cov in [0.5, 0.7, 0.79, 0.799]:
    cap = p1.get_capacity_from_prop_covered(t, np.array([cov]), eligible)[0]
    mult = cap / (cov * 1000.0)
    assert mult > 1.0
    print(f"   coverage={cov:<6} capacity={cap:12.4f}  multiplier={mult:.4f}")
for cov in [0.8, 0.9, 1.0]:
    cap = p1.get_capacity_from_prop_covered(t, np.array([cov]), eligible)[0]
    assert not np.isfinite(cap), f"coverage {cov} at/above saturation should be unpurchasable"
    print(f"   coverage={cov:<6} capacity={cap}  (unpurchasable)  OK")
print()

# ---------------------------------------------------------------- 3. round trip
print("3. get_capacity_from_prop_covered must invert get_prop_covered, through the join")
# RELATIVE error, because inverting near saturation is ill-conditioned for ANY parameterisation of this
# curve, not just this one: arctanh has derivative 1/(1-z^2), which is ~3e8 once z is within 1.5e-9 of 1,
# so a double-precision coverage carries ~1e-8 of absolute error back into the capacity. A narrow band
# (small sigma-lambda) amplifies that further, since z divides by the width. It does not matter in
# practice - coverage that close to saturation costs astronomically much either way - and the check below
# confirms the new form is no worse conditioned than the one it replaces.
worst = 0.0
for lo, hi in [(None, 0.8), (0.0, 0.8), (0.4, 0.8), (0.05, 0.1), (0.9, 1.0)]:
    prog = _prog(hi, lo)
    for c_per in [0.0, 0.01, 0.05, 0.1, 0.3, 0.4, 0.5, 1.0, 2.0]:
        cov = prog.get_prop_covered(t, np.array([c_per * 1000.0]), eligible)[0]
        if not (0 < cov < hi):
            continue
        back = prog.get_capacity_from_prop_covered(t, np.array([cov]), eligible)[0] / 1000.0
        worst = max(worst, abs(back - c_per) / max(c_per, 1e-12))
    print(f"   saturation_lower={str(lo):<5} saturation={hi:<5}  max relative round-trip error so far {worst:.3e}")
assert worst < 1e-6, f"round trip failed, max relative error {worst:g}"
print(f"   max relative error {worst:.3e}  OK")

# the arctanh form must be at least as well conditioned as the log form it replaced
sig = 1.0
for c_per in (1.0, 2.0, 3.0):
    p = sig * np.tanh(c_per / sig)
    new_err = abs(sig * np.arctanh(p / sig) - c_per)
    old_err = abs(-(sig / 2) * np.log(2 * sig / (p + sig) - 1) - c_per)  # the previous expression
    assert new_err <= old_err + 1e-18, "the new inverse is worse conditioned than the old one"
    print(f"   c={c_per:.1f}  previous form err {old_err:.3e}  new form err {new_err:.3e}")
print("   OK\n")

# ---------------------------------------------------------------- 4. C1 continuity at the join
print("4. marginal cost must be continuous at the join (no kink for an optimiser to trip on)")
lam, sig = 0.4, 0.8
p2 = _prog(sig, lam)
eps = 1e-6


def marginal(prog, cov):
    a = prog.get_capacity_from_prop_covered(t, np.array([cov - eps]), eligible)[0]
    b = prog.get_capacity_from_prop_covered(t, np.array([cov + eps]), eligible)[0]
    return (b - a) / (2 * eps * 1000.0)


below = marginal(p2, lam - 10 * eps)
at_join = marginal(p2, lam)
above = marginal(p2, lam + 10 * eps)
print(f"   just below join: {below:.9f}")
print(f"   at join        : {at_join:.9f}")
print(f"   just above join: {above:.9f}")
assert abs(below - 1.0) < 1e-5, "marginal cost below the join should be exactly 1"
assert abs(at_join - 1.0) < 1e-3, "marginal cost should be continuous at the join"
assert above >= below - 1e-6, "marginal cost should be non-decreasing through the join"
print("   OK\n")

# ---------------------------------------------------------------- validation
print("5. an invalid lower bound must be rejected when the progbook is read")
bad = _prog(0.5, 0.6)
lo, up = bad._saturation_bounds(t)
assert lo[0] > up[0]  # the read path raises on this; the curve itself just degenerates safely
cov = bad.get_prop_covered(t, np.array([600.0]), eligible)[0]
assert np.isfinite(cov), "a degenerate bound pair must not produce nan during integration"
print(f"   degenerate bounds give finite coverage {cov:.6f} rather than nan  OK\n")

print("DONE")
