import atomica.ui as au
from atomica.ui import ProjectFramework, Project
import sciris.core as sc

# Get a Result
F = ProjectFramework("./frameworks/framework_tb.xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_tb.xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

# Make some plots from plot names and groups in the Framework
# result.plot(plot_name='plot5',project=P)
# result.plot(plot_name='plot5',pops='all',project=P)
# result.plot(plot_name='plot19',pops='all',project=P)
# result.plot(plot_group='latency')

# Export limited set of results based on 'Export' column in Framework, or export everything
result.export(filename='./temp/export_from_framework.xlsx') # Export only the quantities tagged as 'export' in the Framework
result.export_raw(filename='./temp/export_raw.xlsx') # Export everything

# Plot various cascades
au.plot_cascade(result,cascade='main',pops='all',year=2000)
au.plot_cascade(result,cascade='main',pops='all',year=2030)
au.plot_cascade(result,cascade='main',pops='0-4',year=2030)
au.plot_cascade(result,cascade='secondary',pops='0-4',year=2030)

# Dynamically create a cascade
cascade = sc.odict()
cascade['Susceptible'] = 'sus'
cascade['Vaccinated'] = 'vac'
cascade['Infected'] = 'ac_inf'
au.plot_cascade(result,cascade=cascade,pops='all',year=2030)


