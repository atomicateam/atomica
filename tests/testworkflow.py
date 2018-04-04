"""
Version:
"""

import atomica.ui as aui
import sciris.core as sc
import os

torun = [
"makeframeworkfile",
"makeframework",
"saveframework",
"loadframework",
"makedatabook",
"makeproject",
"saveproject",
"loadproject",
]

tmpdir = "." + os.sep + "temp" + os.sep


if "makeframeworkfile" in torun:
    framework_instructions, _ = aui.makeInstructions(framework=None, data=None, workbook_type=aui.SystemSettings.STRUCTURE_KEY_FRAMEWORK)
    framework_instructions.updateNumberOfItems("par", 7)        # Set the number of parameters
    framework_instructions.updateNumberOfItems("comp", 4)       # Set the number of compartments
    framework_instructions.updateNumberOfItems("charac", 7)     # Set the number of characteristics
    
    aui.writeWorkbook(workbook_path=tmpdir+"framework_test.xlsx", framework=None, data=None, instructions=framework_instructions, workbook_type=aui.SystemSettings.STRUCTURE_KEY_FRAMEWORK)


	
if "makeframework" in torun:
    F = aui.ProjectFramework(name="SIR", frameworkfilename="./frameworks/framework_sir.xlsx")


if "saveframework" in torun:
    F.save(tmpdir+"testframework.frw")


if "loadframework" in torun:
    F = sc.loadobj(tmpdir+"testframework.frw")


if "makedatabook" in torun:
    F = sc.loadobj(tmpdir+"testframework.frw")
    P = aui.Project(framework=F) # Create a project with no data
    databook_instructions, _ = aui.makeInstructions(framework=F, data=None, workbook_type=aui.SystemSettings.STRUCTURE_KEY_DATA)
    databook_instructions.updateNumberOfItems("prog", 3)    # Set the number of programs
    databook_instructions.updateNumberOfItems("pop", 1)     # Set the number of populations
    P.createDatabook(databook_path="./databooks/databook_sir_blank.xlsx", instructions=databook_instructions, databook_type=aui.SystemSettings.DATABOOK_DEFAULT_TYPE)


if "makeproject" in torun:
    P = aui.Project(framework=F, databook="./databooks/databook_sir.xlsx")
    
    for var in ["sus","inf","rec","dead","ch_all","foi"]:
        P.results[0].getPop("adults").getVariable(var)[0].plot()

if "saveproject" in torun:
    P.save(tmpdir+"testproject.prj")


if "loadproject" in torun:
    P = sc.loadobj(tmpdir+"testproject.prj")

