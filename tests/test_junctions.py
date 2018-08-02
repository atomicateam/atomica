import atomica.ui as au
from atomica.core.excel import AtomicaSpreadsheet, transfer_comments
import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData, PlotData, plot_series
import sciris.core as sc

F_path = "./frameworks/framework_junction_test.xlsx"
D_path = './temp/databook_junction_test.xlsx'

F = ProjectFramework(F_path)
# D = ProjectData.new(F,np.arange(2000,2001),pops={'pop1':'Population 1'},transfers=0)
# D.save(D_path)

P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path=D_path, make_default_parset=True, do_run=True)

res = P.results[0]

d = PlotData(res,[':a',':b','b:',':c',':e'],project=P)
plot_series(d,axis='pops')