import atomica.ui as au
from atomica.ui import ProjectFramework, Project
import sciris.core as sc

# Get a Result
F = ProjectFramework("./frameworks/framework_tb.xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_tb.xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

# # Do a scenario to get a second set of results
par_results = P.results[-1]

scvalues = dict()
scen_par = "doth_rate"
scen_pop = "0-4"
scvalues[scen_par] = dict()
scvalues[scen_par][scen_pop] = dict()
scvalues[scen_par][scen_pop]["y"] = [0.5,0.5]
scvalues[scen_par][scen_pop]["t"] = [1999., 2050.]
P.make_scenario(which='parameter',name="Increased deaths", instructions=scvalues)
scen_results = P.run_scenario(scenario="Increased deaths", parset="default")
par_results.name = 'Baseline'
scen_results.name = 'Scenario'

# Make some plots from plot names and groups in the Framework
result.plot(plot_name='plot5',project=P)
result.plot(plot_name='plot5',pops='all',project=P)
result.plot(plot_name='plot19',pops='all',project=P)
result.plot(plot_group='latency')

# Export limited set of results based on 'Export' column in Framework, or export everything
result.export(filename='./temp/export_from_framework.xlsx') # Export only the quantities tagged as 'export' in the Framework
result.export_raw(filename='./temp/export_raw.xlsx') # Export everything

# Plot various cascades
au.plot_cascade(result,cascade='main',pops='0-4',year=2030,data=P.data)
au.plot_cascade(result,cascade='main',pops='all',year=2000,data=P.data)
au.plot_cascade(result,cascade='main',pops='all',year=2030,data=P.data)
au.plot_cascade(result,cascade='secondary',pops='0-4',year=2030,data=P.data)

# # Dynamically create a cascade
cascade = sc.odict()
cascade['Susceptible'] = 'sus'
cascade['Vaccinated'] = 'vac'
cascade['Infected'] = 'ac_inf'
au.plot_cascade(result,cascade=cascade,pops='all',year=2030)

au.plot_multi_cascade([par_results,scen_results],'main',year=2018)
au.plot_multi_cascade([par_results],'main',year=[2018,2020])
au.plot_multi_cascade([par_results],'secondary',year=[2018,2020])
au.plot_multi_cascade([par_results,scen_results],cascade=cascade,pops='all',year=2030)

au.plot_multi_cascade([par_results,scen_results],cascade='main',pops='all',year=[2018,2020])
