import atomica.ui as au
from atomica.core.excel import AtomicaSpreadsheet, transfer_comments
import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData
import sciris.core as sc

F = ProjectFramework("./frameworks/framework_tb.xlsx")
#
# Copy a databook by loading and saving it
data = ProjectData.from_spreadsheet("./databooks/databook_tb.xlsx",F)
data.save('./temp/d_blug.xlsx')

# Copy comments, using lower-level AtomicaSpreadsheet (for in-memory file operations)
original_workbook = AtomicaSpreadsheet("./databooks/databook_tb.xlsx")
new_workbook = data.to_spreadsheet() # This is a AtomicaSpreadsheet that can be stored in the FE database
transfer_comments(new_workbook,original_workbook)
new_workbook.save('./temp/d_blug_formatted.xlsx')

# Run the copied databook
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./temp/d_blug.xlsx", make_default_parset=True, do_run=True)
d = au.PlotData(P.results["parset_default"], pops='0-4')
au.plot_series(d, plot_type="stacked") # This should look like the usual Optima-TB result

# Change the time axis
d2 = sc.dcp(data)
d2.change_tvec(np.arange(2000,2017,0.5))
d2.save('./temp/d_blug_halfyear.xlsx')

# Run the half-year databook
P = Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path="./temp/d_blug_halfyear.xlsx", make_default_parset=True, do_run=True)
d = au.PlotData(P.results["parset_default"], pops='0-4')
au.plot_series(d, plot_type="stacked") # This should look like the usual Optima-TB result

# Remove some key pops
d2 = sc.dcp(data)
d2.remove_pop('Pris')
d2.remove_pop('Pris (HIV+)')
d2.save('./temp/d_blug_nopris.xlsx')

# Remove a transfer, add an interaction, add a pop
d2.remove_transfer('hiv_inf')
d2.add_interaction('d_ctc','New interpop')
d2.add_pop('asdf','The ASDF pop')
d2.save('./temp/d_blug_newpop.xlsx')

# Make a brand new databook
data = ProjectData.new(F,np.arange(2000,2017),pops=2,transfers=4)
data.save('./temp/d_blug_blank.xlsx')

# Modify incomplete databook
d2 = ProjectData.from_spreadsheet('./temp/d_blug_blank.xlsx',F)
d2.add_pop('asdf','The ASDF pop')
d2.add_interaction('d_ctc','New interpop')
d2.save('./temp/d_blug_blank_modified.xlsx')
