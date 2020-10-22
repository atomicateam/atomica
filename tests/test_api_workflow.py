"""
Note, need to run testworkflow.py first to generate the required files
"""

# Imports
import atomica as at
import os

# Setup
plot_initial = True

test = "sir"  # This test workflow only works with the SIR model

testdir = at.parent_dir()
tmpdir = testdir / "temp"

F = at.ProjectFramework(at.LIBRARY_PATH / test + "_framework.xlsx")
P = at.Project(name=test.upper() + " project", framework=F, do_run=False)
P.load_databook(databook_path=at.LIBRARY_PATH / test + "_databook.xlsx", make_default_parset=True, do_run=True)

at.export_results(P.results[0], tmpdir / test.upper() + " results")

P.save(tmpdir / test + ".prj")
P = at.Project.load(tmpdir / test + ".prj")

if plot_initial:

    for var in ["sus", "inf", "rec", "dead", "ch_all", "foi"]:
        P.results[0].get_variable(var, "adults")[0].plot()

    # Plot decomposition of population
    d = at.PlotData(P.results[0], outputs=["sus", "inf", "rec", "dead"], project=P)
    at.plot_series(d, plot_type="stacked")

    # Bar plot showing deaths, disaggregated by source compartment
    d = at.PlotData(P.results[0], outputs=["sus:dead", "inf:dead", "rec:dead"], t_bins=10, project=P)
    at.plot_bars(d, outer="results", stack_outputs="all")

    # Aggregate flows
    d = at.PlotData(P.results[0], outputs=[{"Death rate": ["infdeath:flow", "susdeath:flow"]}], project=P)
    at.plot_series(d)

    # Demonstrate how susdeath:flow sums over all of the tags sharing that label
    d = at.PlotData(P.results[0], outputs=["susdeath:flow"], project=P)
    at.plot_series(d)

    # Summing over the transitions between compartments in susdeath gives the same result
    d = at.PlotData(P.results[0], outputs=["sus:dead", "rec:dead"], project=P)
    at.plot_series(d, plot_type="stacked")

    # Summing via a function aggregation does the same thing
    d = at.PlotData([P.results[0]], outputs={"Susdeaths": "sus:dead+rec:dead"})
    at.plot_series(d)


# Make a scenario e.g. decreased infection rate
scvalues = dict()
scvalues["infdeath"] = dict()
scvalues["infdeath"]["adults"] = dict()
scvalues["infdeath"]["adults"]["y"] = [0.125]
scvalues["infdeath"]["adults"]["t"] = [2015.0]

scvalues["infdeath"]["adults"]["y"] = [0.125, 0.5]
scvalues["infdeath"]["adults"]["t"] = [2015.0, 2020.0]
scvalues["infdeath"]["adults"]["smooth_onset"] = [2, 3]

scvalues["infdeath"]["adults"]["y"] = [0.125, 0.25, 0.50, 0.50]
scvalues["infdeath"]["adults"]["t"] = [2015.0, 2020.0, 2025.0, 2030.0]
scvalues["infdeath"]["adults"]["smooth_onset"] = [4.0, 3.0, 2.0, 1.0]

s = at.ParameterScenario("increased_infections", scvalues)
s.run(project=P, parset=P.parsets["default"])

d = at.PlotData(P.results, outputs=["infdeath"])
at.plot_series(d, axis="results")

d = at.PlotData(P.results, outputs=["inf"])
at.plot_series(d, axis="results")

d = at.PlotData(P.results, outputs=["dead"])
at.plot_series(d, axis="results")

# plt.show()

# Synthesize the calibration target
# P.parsets['calibration_target'] = dcp(P.parsets[0])
# P.parsets['calibration_target'].name = 'calibration_target'
# par = P.parsets['calibration_target'].get_par('transpercontact')
# par.y_factor['adults']=0.2
# r2 = P.run_sim(parset='calibration_target')
# d = PlotData([P.results[0],r2], outputs=['ch_prev'])
# plot_series(d, axis='results',data=P.data)


# Perform calibration to get a calibrated parset
pars_to_adjust = [("transpercontact", "adults", 0.1, 1.9)]
output_quantities = []
for pop in P.parsets[0].pop_names:
    output_quantities.append(("ch_prev", pop, 1.0, "fractional"))
calibrated_parset = at.calibrate(P, P.parsets[0], pars_to_adjust, output_quantities, max_time=30)

# Plot the results before and after calibration
calibrated_results = P.run_sim(calibrated_parset)
d = at.PlotData([P.results[0], calibrated_results], outputs=["ch_prev"])
at.plot_series(d, axis="results", data=P.data)
