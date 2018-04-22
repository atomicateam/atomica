"""
Version:
"""

import atomica.ui as aui
import os

torun = [
"makeframeworkfile",
"makeframework",
"saveframework",
"loadframework",
"makedatabook",
"makeproject",
"makeplots",
"saveproject",
"loadproject",
]

tmpdir = "." + os.sep + "temp" + os.sep

if "makeframeworkfile" in torun:
    # Choosing an excess of template objects to prove that it is fine to delete them when constructing framework file.
    aui.ProjectFramework.createTemplate(path=tmpdir+"framework_tb_blank.xlsx", num_comps=40, num_pars=140, num_characs=60)
    
if "makeframework" in torun:
    F = aui.ProjectFramework(name="TB", file_path="./frameworks/framework_tb.xlsx")

if "saveframework" in torun:
    F.save(tmpdir+"tb.frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+"tb.frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with no data
    P.createDatabook(databook_path="./databooks/databook_tb_blank.xlsx", num_pops=1, num_progs=3)

if "makeproject" in torun:
    P = aui.Project(framework=F, databook="./databooks/databook_tb.xlsx")
    
if "makeplots" in torun:
    for var in ["sus","inf","rec","dead","ch_all","foi"]:
        P.results[0].getPop("adults").getVariable(var)[0].plot()

if "saveproject" in torun:
    P.save(tmpdir+"testproject.prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+"testproject.prj")

