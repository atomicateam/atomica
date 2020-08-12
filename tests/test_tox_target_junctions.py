import atomica as at
import numpy as np
import sciris as sc

testdir = at.parent_dir()
tmpdir = testdir / 'temp'

F = at.ProjectFramework(testdir / 'target_junctions_test_framework.xlsx')
D = at.ProjectData.new(framework=F, tvec=[2019], pops=1, transfers=0)

# PS = at.ProgramSet.new(framework=F,data=D,tvec=[2019],progs=2)
# PS.save(testdir / 'target_junctions_test_progbook.xlsx')

P = at.Project(framework=F.to_spreadsheet(), databook=D.to_spreadsheet())
P.load_progbook(testdir / 'target_junctions_test_progbook.xlsx')

baseline = P.run_sim(parset='default', progset='default', progset_instructions=at.ProgramInstructions(start_year=2019, alloc={'Prog 1': 0, 'Prog 2': 0}))


# def test_target_junctions():
#     F = at.ProjectFramework(at.LIBRARY_PATH / 'tb_framework.xlsx')
#     D = at.ProjectData.from_spreadsheet(at.LIBRARY_PATH / 'tb_databook.xlsx', framework=F)
#     D.validate(F)  # Need to validate the databook before it can be used for anything other than databook IO

#
#
# if __name__ == '__main__':
#     test_progbooks()
