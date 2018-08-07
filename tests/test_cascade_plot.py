import atomica.ui as au
from atomica.ui import ProjectFramework, Project
import sciris.core as sc

#test = 'tb'
test = 'udt'

torun = [
#"basicplots",
"scenplots",
#"cascadefromscratch",
#'mpld3test'
]

# Load a framework and project to get a Result
F = ProjectFramework("./frameworks/framework_"+test+".xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_"+test+".xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

# # Make some plots from plot names and groups in the Framework
if "basicplots" in torun and test=='tb':
    result.plot(plot_name='plot5',project=P)
    result.plot(plot_name='plot5',pops='all',project=P)
    result.plot(plot_name='plot19',pops='all',project=P)
    result.plot(plot_group='latency')

#    # Export limited set of results based on 'Export' column in Framework, or export everything
#    result.export(filename='./temp/export_from_framework.xlsx') # Export only the quantities tagged as 'export' in the Framework
#    result.export_raw(filename='./temp/export_raw.xlsx') # Export everything

    # Plot various cascades
    startyear = 2000 if test=='tb' else 2016
    endyear = 2030 if test=='tb' else 2017
    au.plot_cascade(result,cascade='main',pops='all',year=startyear,data=P.data)
    au.plot_cascade(result,cascade='main',pops='all',year=endyear,data=P.data)
    if test=='tb': 
        au.plot_cascade(result,cascade='main',pops='0-4',year=endyear,data=P.data)
        au.plot_cascade(result,cascade='secondary',pops='0-4',year=endyear,data=P.data)
    

# Do a scenario to get a second set of results
if "scenplots" in torun:

    par_results = P.results[-1]
    scvalues = dict()

    if test=='tb':
        scen_par = "doth_rate"
        scen_pop = "0-4"
    elif test=='udt':
        scen_par = "num_diag"
        scen_pop = "adults"
    
    scvalues[scen_par] = dict()
    scvalues[scen_par][scen_pop] = dict()
    if test=='tb':
        scvalues[scen_par][scen_pop]["y"] = [0.5,0.5]
        scvalues[scen_par][scen_pop]["t"] = [1999., 2050.]
        P.make_scenario(which='parameter',name="Increased deaths", instructions=scvalues)
        scen_results = P.run_scenario(scenario="Increased deaths", parset="default")
    elif test=='udt':
        scvalues[scen_par][scen_pop]["y"] = [1000.,1500.]
        scvalues[scen_par][scen_pop]["t"] = [2016., 2017.]
        P.make_scenario(which='parameter',name="Increased diagnosis rate", instructions=scvalues)
        scen_results = P.run_scenario(scenario="Increased diagnosis rate", parset="default")

    par_results.name = 'Baseline'
    scen_results.name = 'Scenario'
    startyear = 2018 if test=='tb' else 2016
    endyear = 2020 if test=='tb' else 2017

    au.plot_multi_cascade([par_results,scen_results],'main',year=startyear)
    au.plot_multi_cascade([par_results],'main',year=[startyear,endyear])
    if test=='tb': au.plot_multi_cascade([par_results],'secondary',year=[startyear,endyear])
    au.plot_multi_cascade([par_results,scen_results],cascade='main',pops='all',year=[startyear,endyear])
    #au.plot_multi_cascade([par_results,scen_results],cascade=cascade,pops='all',year=2030)



# # Dynamically create a cascade
if "cascadefromscratch" in torun:
    cascade = sc.odict()
    cascade['Susceptible'] = 'sus'
    cascade['Vaccinated'] = 'vac'
    cascade['Infected'] = 'ac_inf'
    au.plot_cascade(result,cascade=cascade,pops='all',year=2030)



if 'mpld3test' in torun:
    P = au.demo()
    au.plot_cascade(P.result(),cascade='main',pops='all',year=2030,data=P.data)
    
    as_mpld3 = True
    if as_mpld3:
        import sciris.weblib.quickserver as sqs
        import pylab as pl
        fig = pl.gcf()
        sqs.browser(fig, mpld3_url='http://localhost:8080/static/mpld3.v0.4.1.js')
