# -*- coding: utf-8 -*-
"""Prototype: coverage-based optimization with a total-spend budget.

Demonstrates the three new pieces on the built-in TB demo:
  1. ProgramSet.get_spend_from_coverage()  - cost a coverage scenario (previously reported no cost at all)
  2. CoverageAdjustment                    - make coverage (not spending) the ASD adjustable
  3. rescale_coverage_to_budget()          - enforce a budget by fixed-point solve, since the implied
                                             spend is only knowable after running

Round-trip check: take a normal spend-driven run, read off the coverage it produced, feed that coverage
back in as an overwrite, and confirm the inversion recovers the original spending.
"""
import numpy as np
import sciris as sc
import atomica as at
from atomica.optimization import CoverageAdjustment, rescale_coverage_to_budget, coverage_spend

P = at.demo(which="tb", do_run=False)
parset = P.parsets[0]
progset = P.progsets[0]
START = 2018.0

print("=" * 78)
print("1. ROUND TRIP:  spend -> coverage -> spend")
print("=" * 78)

# --- baseline: ordinary spend-driven run ---
instr_spend = at.ProgramInstructions(start_year=START)
res_spend = P.run_sim(parset=parset, progset=progset, progset_instructions=instr_spend, result_name="spend_driven")

# what coverage did that produce?
elig = progset.get_num_eligible(res_spend)
caps = progset.get_capacities(tvec=res_spend.model.t, dt=res_spend.model.dt, instructions=instr_spend)
prop = progset.get_prop_coverage(tvec=res_spend.model.t, dt=res_spend.model.dt, capacities=caps, num_eligible=elig, instructions=None)

ti = int(np.argmin(abs(res_spend.model.t - START)))
alloc = progset.get_alloc(res_spend.model.t, instr_spend)

print(f"\n{'program':<24}{'eligible':>12}{'coverage':>10}{'spend $/yr':>14}")
testable = []
for name, prog in progset.programs.items():
    e, c, a = elig[name][ti], prop[name][ti], alloc[name][ti]
    print(f"  {name:<22}{e:12,.0f}{c:10.3f}{a:14,.0f}")
    if e > 0 and 0 < c < 1:
        testable.append(name)

# --- feed the coverage back in and invert it ---
# NB coverage overwrites for ONE-OFF programs are specified in /year units and are multiplied by dt during
# integration (ProgramSet.get_prop_coverage), so to reproduce an observed per-timestep coverage the
# instruction value must be divided by dt. This is an easy trap when writing coverage scenarios by hand.
dt = res_spend.model.dt
instr_cov = at.ProgramInstructions(start_year=START, coverage={n: at.TimeSeries(t=START, vals=(prop[n][ti] / dt if progset.programs[n].is_one_off else prop[n][ti])) for n in testable})
res_cov = P.run_sim(parset=parset, progset=progset, progset_instructions=instr_cov, result_name="coverage_driven")
spend_back = progset.get_spend_from_coverage(res_cov, instructions=instr_cov, tvec=np.array([START]))

print(f"\n{'program':<24}{'orig spend':>14}{'recovered':>14}{'rel err':>10}")
for n in testable:
    orig, back = alloc[n][ti], float(spend_back[n][0])
    err = abs(back - orig) / orig if orig else np.nan
    flag = "  OK" if err < 0.02 else "  <-- differs"
    print(f"  {n:<22}{orig:14,.0f}{back:14,.0f}{err:10.1%}{flag}")
print("\n  (differences arise where the epidemic shifts between the two runs, changing the eligible pool)")

print()
print("=" * 78)
print("2. BUDGET-CONSTRAINED COVERAGE  (fixed-point rescaling)")
print("=" * 78)

base_spend = coverage_spend(res_cov, progset=progset, instructions=instr_cov, t=START)
print(f"\nspend implied by the baseline coverages: ${base_spend:,.0f}/yr")

for frac in [0.6, 1.4]:
    budget = base_spend * frac
    print(f"\n--- target budget = {frac:.0%} of baseline = ${budget:,.0f}/yr ---")
    scaled, alpha, achieved = rescale_coverage_to_budget(P, parset, progset, instr_cov, budget=budget, t=START, tol=5e-3, verbose=False)
    print(f"  converged: alpha={alpha:.4f}  achieved=${achieved:,.0f}/yr  (error {abs(achieved-budget)/budget:.2%})")
    print(f"  {'program':<22}{'coverage before':>16}{'after':>10}")
    for n in testable:
        print(f"    {n:<20}{instr_cov.coverage[n].vals[0]:16.3f}{scaled.coverage[n].vals[0]:10.3f}")

print()
print("=" * 78)
print("3. CoverageAdjustment wiring")
print("=" * 78)
adj = CoverageAdjustment(testable[0], t=START, lower=0.0, upper=1.0, initial=prop[testable[0]][ti])
test_instr = sc.dcp(instr_cov)
adj.update_instructions([0.42], test_instr)
print(f"\n  CoverageAdjustment('{testable[0]}') -> instructions.coverage = {test_instr.coverage[testable[0]].vals}")
print(f"  initialization from instructions: {adj.get_initialization(progset, instr_cov)}")
print("\nDONE")
