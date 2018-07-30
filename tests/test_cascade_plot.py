import atomica.ui as au
from atomica.core.excel import AtomicaSpreadsheet, transfer_comments
import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData
import sciris.core as sc


# Run the copied databook
F = ProjectFramework("./frameworks/framework_tb.xlsx")
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./databooks/databook_tb.xlsx", make_default_parset=True, do_run=True)
result = P.results[0]

au.plot_cascade(result,cascade='main',framework=F,pops='all',year=2000)
au.plot_cascade(result,cascade='main',framework=F,pops='all',year=2030)
au.plot_cascade(result,cascade='main',framework=F,pops='0-4',year=2030)
au.plot_cascade(result,cascade='secondary',framework=F,pops='0-4',year=2030)
