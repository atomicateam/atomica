import atomica as at
import matplotlib.pyplot as plt

proj = at.demo('tb')
par_results = proj.results[-1]

scvalues = dict()
scen_par = "doth_rate"
scen_pop = "0-4"
scvalues[scen_par] = dict()
scvalues[scen_par][scen_pop] = dict()
scvalues[scen_par][scen_pop]["y"] = [0.5,0.5]
scvalues[scen_par][scen_pop]["t"] = [1999., 2050.]
scen = proj.make_scenario(which='parameter',name="Increased deaths", instructions=scvalues)
scen_results = scen.run(proj,proj.parsets["default"])
par_results.name = 'Baseline'
scen_results.name = 'Scenario'
d = at.PlotData([par_results,scen_results],outputs=scen_par,pops=scen_pop)
at.plot_series(d,axis='results')
