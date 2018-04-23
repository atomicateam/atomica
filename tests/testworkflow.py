"""
Version:
"""

import atomica.ui as aui
import os

test = "sir"
#test = "tb"

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
    if test == "sir": aui.ProjectFramework.createTemplate(path=tmpdir+"framework_sir_blank.xlsx", num_comps=4, num_pars=6, num_characs=8)
    elif test == "tb": aui.ProjectFramework.createTemplate(path=tmpdir+"framework_tb_blank.xlsx", num_comps=40, num_characs=60, num_pars=140, num_datapages=10)
    
if "makeframework" in torun:
    F = aui.ProjectFramework(name=test.upper(), file_path="./frameworks/framework_"+test+".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with no data
    if test == "sir": P.createDatabook(databook_path=tmpdir+"databook_sir_blank.xlsx", num_pops=1, num_progs=3)
    elif test == "tb": P.createDatabook(databook_path=tmpdir+"databook_tb_blank.xlsx", num_pops=7, num_progs=14)

if "makeproject" in torun:
    P = aui.Project(name=test.upper()+" project", framework=F, databook="./databooks/databook_"+test+".xlsx")
    
if "makeplots" in torun:
    for var in ["sus","inf","rec","dead","ch_all","foi"]:
        P.results[0].getVariable("adults",var)[0].plot()

if "export" in torun:
    P.results[0].export(tmpdir+test+"_results")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+test+".prj")