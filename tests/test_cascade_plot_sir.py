import atomica.ui as au
from atomica.ui import ProjectFramework, Project

# Get a Result
F = ProjectFramework("./frameworks/framework_sir_dynamic.xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_sir_dynamic.xlsx", make_default_parset=True, do_run=True)
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
scen_results = scen.run(P,P.parsets["default"])
par_results.name = 'Baseline'
scen_results.name = 'Scenario'

# Single cascades with data
au.plot_cascade(par_results,cascade='main',pops='adults',year=2017,data=P.data)
au.plot_cascade(scen_results,cascade='main',pops='adults',year=2017,data=P.data)

# Single cascades without data
au.plot_cascade(par_results,cascade='main',pops='adults',year=2025,data=P.data)
au.plot_cascade(scen_results,cascade='main',pops='adults',year=2025,data=P.data)

au.plot_multi_cascade([par_results,scen_results],cascade='main',pops='adults',year=[2017,2025],data=P.data)

d = au.PlotData(par_results,outputs=['sus','inf','rec','dead'])
au.plot_series(d,plot_type='stacked')

d = au.PlotData(scen_results,outputs=['sus','inf','rec','dead'])
au.plot_series(d,plot_type='stacked')

# Single cascade series
au.plot_single_cascade_series(par_results,cascade='main',pops='adults',data=P.data)

