import atomica as at
from atomica import ProjectFramework
import sciris as sc
from atomica import InvalidCascade
import os

testdir = at.parent_dir()
tmpdir = os.path.join(testdir,'temp','')

try:
    os.makedirs(tmpdir)
except:
    pass

def test_cascade_validate():
    from atomica.cascade import validate_cascade

    # First check that all of the library frameworks are OK
    fnames = os.listdir(at.LIBRARY_PATH)
    # NB. To test a single file, set e.g. `fnames=['framework_tb.xlsx']`
    for fname in fnames:
        if fname.endswith('_framework.xlsx'):
            print("Validating %s" % (fname))
            F = ProjectFramework(at.LIBRARY_PATH+fname)

            # Validate all of the cascades in the framework
            for cascade in F.cascades:
                validate_cascade(F, cascade)


    F = ProjectFramework(at.LIBRARY_PATH + "tb_framework.xlsx")
    try:
        validate_cascade(F,None) # Try running this on the command line to see the error message
    except InvalidCascade:
        print("Correctly raised invalid TB fallback cascade")

    for fname in ["framework_sir_badcascade1.xlsx","framework_sir_badcascade2.xlsx"]:
        try:
            F = ProjectFramework(at.parent_dir() + fname)
        except InvalidCascade:
            print("Correctly raised invalid cascade for %s" % fname)

def test_cascade_basic_tb():
    P = at.demo('tb')
    result = P.results[-1]

    result.plot(plot_name='Active DS-TB',project=P)
    result.plot(plot_name='Active DS-TB',pops='all',project=P)
    result.plot(plot_group='latency')

#    # Export limited set of results based on 'Export' column in Framework, or export everything
    at.export_results(result,filename=tmpdir+'export_from_framework_1.xlsx' )
    result.export_raw(filename=tmpdir+'export_raw.xlsx') # Export everything

    # Plot various cascades
    startyear = 2000
    endyear = 2030

    at.plot_cascade(result, cascade='TB treatment (including recovered)', pops='all', year=startyear, data=P.data)
    at.plot_cascade(result, cascade='TB treatment (including recovered)', pops='all', year=endyear, data=P.data)

    at.plot_cascade(result,cascade='TB treatment (including recovered)',pops='0-4',year=endyear,data=P.data)
    at.plot_cascade(result,cascade='SP treatment',pops='0-4',year=endyear,data=P.data)

    at.plot_cascade(result,cascade='SP treatment',pops='Children 5-14',year=endyear,data=P.data) # Look up using full name
    at.plot_cascade(result,cascade='SP treatment',pops=['Children 0-4','Children 5-14'],year=endyear,data=P.data) # Combine subset of pops - should be able to add numbers from the previous two figures

def test_cascade_basic_udt():
    P = at.demo('udt')
    result = P.results[-1]
    at.plot_cascade(result, pops='all', year=2016, data=P.data)  # plot default cascade

def test_cascade_scen_tb():

    P = at.demo('tb')
    par_results = P.results[-1]

    scvalues = dict()
    scen_par = "doth_rate"
    scen_pop = "0-4"

    scvalues[scen_par] = dict()
    scvalues[scen_par][scen_pop] = dict()
    scvalues[scen_par][scen_pop]["y"] = [0.5,0.5]
    scvalues[scen_par][scen_pop]["t"] = [1999., 2050.]
    scen = P.make_scenario(which='parameter',name="Increased deaths", instructions=scvalues)
    scen_results = scen.run(P,P.parsets["default"])

    par_results.name = 'Baseline'
    scen_results.name = 'Scenario'
    startyear = 2018
    endyear = 2020

    at.plot_multi_cascade([par_results,scen_results],None,year=startyear)
    at.plot_multi_cascade([par_results],None,year=[startyear,endyear])
    at.plot_multi_cascade([par_results,scen_results],cascade=0,pops='all',year=[startyear,endyear])
    at.plot_multi_cascade([par_results],cascade=1,year=[startyear,endyear])

def test_cascade_scen_udt():
    P = at.demo('udt')
    par_results = P.results[-1]
    scvalues = dict()

    scen_par = "num_diag"
    scen_pop = "adults"

    scvalues[scen_par] = dict()
    scvalues[scen_par][scen_pop] = dict()
    scvalues[scen_par][scen_pop]["y"] = [1000., 1500.]
    scvalues[scen_par][scen_pop]["t"] = [2016., 2017.]
    scen = P.make_scenario(which='parameter', name="Increased diagnosis rate", instructions=scvalues)
    scen_results = scen.run(P, P.parsets["default"])

    par_results.name = 'Baseline'
    scen_results.name = 'Scenario'
    startyear = 2016
    endyear = 2017

    at.plot_multi_cascade([par_results, scen_results], None, year=startyear)
    at.plot_multi_cascade([par_results], None, year=[startyear, endyear])

def test_cascade_dynamic():
    # Dynamically create a cascade
    P = at.demo('sir')
    cascade = sc.odict()
    cascade['Everyone'] = ['sus','inf','rec']
    cascade['Ever infected'] = ['inf','rec']
    cascade['Recovered'] = 'rec'
    at.plot_cascade(P.results[-1],cascade=cascade,pops='all',year=2023)

def test_cascade_sir():
    testdir = at.parent_dir()
    tmpdir = os.path.join(testdir, 'temp', '')

    # Get a Result
    F = ProjectFramework(testdir + 'framework_sir_dynamic.xlsx')
    P = at.Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=testdir + "databook_sir_dynamic.xlsx", make_default_parset=True, do_run=True)
    result = P.results[0]

    # # Do a scenario to get a second set of results
    par_results = P.results[-1]

    scvalues = dict()
    scen_par = "infdeath"
    scen_pop = "adults"
    scvalues[scen_par] = dict()
    scvalues[scen_par][scen_pop] = dict()
    scvalues[scen_par][scen_pop]["y"] = [0.2, 0.2]
    scvalues[scen_par][scen_pop]["t"] = [2014., 2050.]
    scen = P.make_scenario(which='parameter', name="Increased mortality", instructions=scvalues)
    scen_results = scen.run(P, P.parsets["default"])
    par_results.name = 'Baseline'
    scen_results.name = 'Scenario'

    # Single cascades with data
    at.plot_cascade(par_results, cascade='main', pops='adults', year=2017, data=P.data)
    at.plot_cascade(scen_results, cascade='main', pops='adults', year=2017, data=P.data)

    # Single cascades without data
    at.plot_cascade(par_results, cascade='main', pops='adults', year=2025, data=P.data)
    at.plot_cascade(scen_results, cascade='main', pops='adults', year=2025, data=P.data)

    at.plot_multi_cascade([par_results, scen_results], cascade='main', pops='adults', year=[2017, 2025], data=P.data)

    d = at.PlotData(par_results, outputs=['sus', 'inf', 'rec', 'dead'])
    at.plot_series(d, plot_type='stacked')

    d = at.PlotData(scen_results, outputs=['sus', 'inf', 'rec', 'dead'])
    at.plot_series(d, plot_type='stacked')

    # Single cascade series
    at.plot_single_cascade_series(par_results, cascade='main', pops='adults', data=P.data)

if __name__ == "__main__":
    test_cascade_validate()
    test_cascade_basic_tb()
    test_cascade_basic_udt()
    test_cascade_scen_tb()
    test_cascade_scen_udt()
    test_cascade_dynamic()
    test_cascade_sir()