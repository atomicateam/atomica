# -*- coding: utf-8 -*-
"""Proportion-unit coverage: annualization depends on stock vs flow, not on the units.

Coverage entered as a 'fraction'/'%' makes a program coverage-driven - the fraction is read straight from
the progbook and the spending becomes the derived quantity. Whether that fraction is a per-year RATE or a
dimensionless PROPORTION depends on what the program targets:

  - ordinary compartment (a STOCK)  -> covering fraction g per year reaches g*dt each timestep -> scale by dt
  - junction/source/sink (a FLOW)   -> fraction of the people passing through, same over a timestep or a
                                       year -> no scaling

This checks the stock case round-trips against the ordinary spend-driven path, which is the behaviour a
proportion-unit program has to reproduce for the two ways of specifying coverage to agree.
"""
import numpy as np
import atomica as at

P = at.demo(which="tb", do_run=False)
parset, progset = P.parsets[0], P.progsets[0]
START = 2018.0

# --- baseline: ordinary spend-driven run, all coverage in people/year ---
instr = at.ProgramInstructions(start_year=START)
res = P.run_sim(parset=parset, progset=progset, progset_instructions=instr, result_name="spend_driven")
dt = res.model.dt
ti = int(np.argmin(abs(res.model.t - START)))
prop = progset.get_prop_coverage(tvec=res.model.t, dt=dt, capacities=progset.get_capacities(tvec=res.model.t, dt=dt, instructions=instr), num_eligible=progset.get_num_eligible(res), instructions=None)

one_off_stock = [n for n, pr in progset.programs.items() if pr.is_one_off and n not in progset.flow_targeted_programs and 0 < prop[n][ti] < 1]
print(f"one-off stock-targeting programs: {one_off_stock}\n")

print("Book coverage as a 'fraction' must reproduce the spend-driven coverage.")
print("For a one-off program on a stock the book value is a /year rate, so realised = book*dt.\n")
print(f"{'program':<22}{'spend-driven':>14}{'book fraction':>15}{'realised':>11}{'rel err':>10}")

for name in one_off_stock:
    target = prop[name][ti]  # per-timestep coverage the spend-driven run produced
    ps = at.ProgramSet.from_spreadsheet(P.progsets[0].to_spreadsheet(), framework=P.framework, data=P.data)
    ps.programs[name].coverage = at.TimeSeries(assumption=target / dt, units="fraction")  # /year rate
    assert ps.programs[name].is_coverage_driven
    r2 = P.run_sim(parset=parset, progset=ps, progset_instructions=at.ProgramInstructions(start_year=START), result_name=f"cov_{name}")
    got = r2.get_coverage("fraction")[name][ti]
    err = abs(got - target) / target
    print(f"  {name:<20}{target:14.5f}{target/dt:15.5f}{got:11.5f}{err:10.2%}" + ("  OK" if err < 1e-9 else "  <-- MISMATCH"))

# --- a flow target must NOT be annualized ---
junction_progs = progset.flow_targeted_programs
print(f"\nflow-targeted (junction/source/sink) programs in this progset: {sorted(junction_progs) or 'none'}")
print("  (for these the book fraction is used as-is - see tests on a model with junction-targeted programs)")
print("\nDONE")
