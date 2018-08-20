import atomica.ui as au
from atomica.ui import ProjectFramework, Project
import sciris.core as sc
from atomica.ui import InvalidCascade
import os

test = 'tb'
# test = 'udt'

torun = [
#"basicplots",
#"scenplots",
"validate_cascade"
# "basicplots",
#"scenplots",
#"cascadefromscratch",
#'mpld3test'
]


# Check validation
if "validate_cascade" in torun:
    from atomica.cascade import validate_cascade

    # Check that all the frameworks have either a valid cascade sheet, or
    # the fallback cascade is valid
    fnames = os.listdir('./frameworks')
    for fname in fnames:
        if '_bad' in fname:
            continue
        print("Validating %s" % (fname))
        F = au.ProjectFramework("./frameworks/framework_tb.xlsx")

#        F = ProjectFramework(sc.makefilepath(fname,'./frameworks'))

        # Validate all of the cascades in the framework
        if not F.cascades:
            validate_cascade(F, None)
        else:
            for cascade in F.cascades:
                validate_cascade(F, cascade)


    F = ProjectFramework("./frameworks/framework_tb.xlsx")
    try:
        validate_cascade(F,None) # Try running this on the command line to see the error message
    except InvalidCascade:
        print("Correctly raised invalid TB fallback cascade")

    for fname in ["./frameworks/framework_sir_badcascade1.xlsx","./frameworks/framework_sir_badcascade2.xlsx"]:
        F = ProjectFramework(fname)
        try:
            if not F.cascades:
                validate_cascade(F, None)
            else:
                for cascade in F.cascades:
                    validate_cascade(F, cascade)
        except InvalidCascade:
            print("Correctly raised invalid cascade for %s" % fname)


# Load a framework and project to get a Result
F = ProjectFramework("./frameworks/framework_"+test+".xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_"+test+".xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

# # Make some plots from plot names and groups in the Framework
if "basicplots" in torun:

    if test=='tb':
        result.plot(plot_name='Active DS-TB',project=P)
        result.plot(plot_name='Active DS-TB',pops='all',project=P)
        result.plot(plot_group='latency')

    #    # Export limited set of results based on 'Export' column in Framework, or export everything
        result.export(filename='./temp/export_from_framework_1.xlsx') # Export only the quantities tagged as 'export' in the Framework
        result.export(filename='./temp/export_from_framework_2.xlsx',plot_names=['Active DS-TB']) # export all cascades but only one plot
        result.export(filename='./temp/export_from_framework_3.xlsx',plot_names=['Active DS-TB','Active treatment'],cascade_names=[]) # Export two plots and no cascades

        result.export_raw(filename='./temp/export_raw.xlsx') # Export everything

        # Plot various cascades
        startyear = 2000
        endyear = 2030

        au.plot_cascade(result, cascade='TB treatment (including recovered)', pops='all', year=startyear, data=P.data)
        au.plot_cascade(result, cascade='TB treatment (including recovered)', pops='all', year=endyear, data=P.data)

        au.plot_cascade(result,cascade='TB treatment (including recovered)',pops='0-4',year=endyear,data=P.data)
        au.plot_cascade(result,cascade='SP treatment',pops='0-4',year=endyear,data=P.data)

        au.plot_cascade(result,cascade='SP treatment',pops='Gen 5-14',year=endyear,data=P.data) # Look up using full name
        au.plot_cascade(result,cascade='SP treatment',pops=['Gen 0-4','Gen 5-14'],year=endyear,data=P.data) # Combine subset of pops - should be able to add numbers from the previous two figures
    elif test == 'udt':
        # No predefined cascades, use the default one
        au.plot_cascade(result, pops='all', year=2016, data=P.data)  # plot default cascade
    else:
        # Plot the first cascade by default
        startyear = 2016
        endyear = 2017
        au.plot_cascade(result, cascade=0, pops='all', year=startyear, data=P.data)
        au.plot_cascade(result, cascade=0, pops='all', year=endyear, data=P.data)


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
    Q = au.demo()
    P.result().name = 'Example result 1'
    Q.result().name = 'Example result 2'
    results = [P.result(), Q.result()]
    fig,table = au.plot_cascade(results, cascade='main', pops='all', year=2030, data=P.data, show_table=False)
    
    as_mpld3 = True
    if as_mpld3:
        import sciris.weblib.quickserver as sqs
        sqs.browser(fig, mpld3_url='http://localhost:8080/static/mpld3.v0.4.1.js')
