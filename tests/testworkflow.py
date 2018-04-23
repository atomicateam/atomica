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
"export",
"saveproject",
"loadproject",
]

tmpdir = "." + os.sep + "temp" + os.sep

if "makeframeworkfile" in torun:
    aui.ProjectFramework.createTemplate(path=tmpdir+"framework_test.xlsx", num_comps=4, num_pars=6, num_characs=8)
    
if "makeframework" in torun:
    F = aui.ProjectFramework(name="SIR", file_path="./frameworks/framework_sir.xlsx")

if "saveframework" in torun:
    F.save(tmpdir+"testframework.frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+"testframework.frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with no data
    P.createDatabook(databook_path="./databooks/databook_sir_blank.xlsx", num_pops=1, num_progs=3)

if "makeproject" in torun:
    P = aui.Project(framework=F, databook="./databooks/databook_sir.xlsx")
    
if "makeplots" in torun:
    for var in ["sus","inf","rec","dead","ch_all","foi"]:
        P.results[0].getVariable("adults",var)[0].plot()

if "export" in torun:
    P.results[0].export('test')
    
if "saveproject" in torun:
    P.save(tmpdir+"testproject.prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+"testproject.prj")