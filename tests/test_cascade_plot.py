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

