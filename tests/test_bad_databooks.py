## This script tests some databook IO operations

import atomica.ui as au
from atomica.excel import transfer_comments
import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData
import sciris as sc

F = ProjectFramework("./frameworks/framework_tb.xlsx")
F.save('./temp/f_blug.xlsx')
#
# Copy a databook by loading and saving it
data = ProjectData.from_spreadsheet("./bad_databooks/extra_tdve_rows.xlsx",F)
data.save('./temp/d_blug.xlsx')
