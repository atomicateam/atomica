import atomica.ui as au
from atomica.ui import ProjectFramework, Project

# Get a Result

F = ProjectFramework(au.atomica_path('tests') + "framework_sir_dynamic.xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path=au.atomica_path('tests') + "databook_sir_dynamic.xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

# # Do a scenario to get a second set of results
par_results = P.results[-1]

scvalues = dict()
scen_par = "infdeath"
scen_pop = "adults"
scvalues[scen_par] = dict()
scvalues[scen_par][scen_pop] = dict()
scvalues[scen_par][scen_pop]["y"] = [0.2,0.2]
scvalues[scen_par][scen_pop]["t"] = [2014., 2050.]
scen = P.make_scenario(which='parameter',name="Increased mortality", instructions=scvalues)
scen_results = scen.run(P,P.parsets['default'])
par_results.name = 'Baseline'
scen_results.name = 'Scenario'

d = au.PlotData([par_results,scen_results],outputs=['sus','inf','rec'],t_bins=10)
au.plot_bars(d,stack_outputs=[['sus','inf']],orientation='horizontal')

