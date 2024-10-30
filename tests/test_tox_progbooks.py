import atomica as at
import numpy as np
import sciris as sc
import pytest

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"


def load_inputs():
    F = at.ProjectFramework(at.LIBRARY_PATH / "tb_framework.xlsx")
    D = at.ProjectData.from_spreadsheet(at.LIBRARY_PATH / "tb_databook.xlsx", framework=F)
    D.validate(F)  # Need to validate the databook before it can be used for anything other than databook IO
    return F, D


def test_remove_program():
    P = at.demo("tb", do_run=False)
    pset = P.progsets[0].copy()
    pset.remove_program("BCG")
    assert "BCG" not in pset.programs
    for covout in pset.covouts.values():
        assert "BCG" not in covout.progs
    P.run_sim(P.parsets[0], pset, at.ProgramInstructions(start_year=2019))


def test_new_workbook():
    F, D = load_inputs()
    P = at.Project(framework=F, databook=D)

    pset = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH / "tb_progbook.xlsx", F, D)
    pset.save(tmpdir / "progbook_test.xlsx")
    pset = at.ProgramSet.from_spreadsheet(tmpdir / "progbook_test.xlsx", F, D)
    pset.save(tmpdir / "progbook_test2.xlsx")

    # Test running a simulation with a newly saved workbook
    P = at.Project(framework=at.LIBRARY_PATH / "tb_framework.xlsx", databook=at.LIBRARY_PATH / "tb_databook.xlsx", do_run=False)
    P.load_progbook(tmpdir / "progbook_test2.xlsx")
    P.run_sim(P.parsets[0], P.progsets[0], at.ProgramInstructions(start_year=2019))


def test_save_new_progbook():
    # Test making a new one
    F, D = load_inputs()
    pset = at.ProgramSet.new(tvec=np.arange(2015, 2018), progs=2, framework=F, data=D)
    pset.save(tmpdir / "progbook_test5.xlsx")


def test_progbooks():
    F, D = load_inputs()
    pset = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH / "tb_progbook.xlsx", F, D)

    # Test adding things
    pset.add_program("newprog", "New Program")
    pset.add_par("newpar", "New Parameter")
    pset.add_pop("newpop", "New Pop")
    pset.save(tmpdir / "progbook_test3.xlsx")

    # Test removing things
    pset.remove_pop("Prisoners")
    pset.remove_comp("Susceptible")
    pset.remove_par("v_num")
    pset.remove_par("LTBI treatment average duration of full course")
    pset.remove_program("BCG")
    pset.save(tmpdir / "progbook_test4.xlsx")

    # Test making a new one
    pset = at.ProgramSet.new(tvec=np.arange(2015, 2018), progs=2, framework=F, data=D)
    pset.save(tmpdir / "progbook_test5.xlsx")

    progs = sc.odict()
    progs["BCG"] = "BCG vaccination"
    progs["PCF"] = "Passive case finding"
    progs["ACF"] = "Active case finding - contact tracing"
    progs["ACF-p"] = "Active case finding - prisoners"
    progs["HospDS"] = "Hospital focused treatment (DS)"
    progs["HospMDR"] = "Hospital focused treatment (MDR)"
    progs["HospXDR"] = "Hospital focused treatment (XDR)"
    progs["AmbDS"] = "Ambulatory treatment (DS)"
    progs["AmbMDR"] = "Ambulatory treatment (MDR)"
    progs["AmbXDR"] = "Ambulatory treatment (XDR)"
    progs["PrisDS"] = "Prisoner treatment (DS)"
    progs["PrisMDR"] = "Prisoner treatment (MD)"
    progs["PrisXDR"] = "Prisoner treatment (XDR)"
    pset = at.ProgramSet.new(tvec=np.arange(2015, 2018), progs=progs, framework=F, data=D)
    pset.save(tmpdir / "progbook_test6.xlsx")

    # Test performance of a random coverage interaction simulation
    P = at.Project(framework=at.LIBRARY_PATH / "tb_framework.xlsx", databook=at.LIBRARY_PATH / "tb_databook.xlsx", do_run=False)
    P.load_progbook(at.LIBRARY_PATH / "tb_progbook.xlsx")
    instructions = at.ProgramInstructions(start_year=2018)
    pset = P.progsets[0]
    for covout in pset.covouts.values():
        covout.cov_interaction = "additive"
    P.run_sim(parset="default", progset="default", progset_instructions=instructions)

    # Test that reloading the a databook works (checking consistency with progbook populations)
    P.load_databook(at.LIBRARY_PATH / "tb_databook.xlsx")

    # THIS DOES VERSIONING
    # which = ['tb','tb_simple','tb_simple_dyn','malaria' ,'hypertension','hypertension_dyn','hiv','hiv_dyn','diabetes','cervicalcancer','udt','udt_dyn','usdt','sir']
    # for a in which:
    #     F = at.ProjectFramework(at.LIBRARY_PATH+'framework_%s.xlsx' % (a))
    #     D = at.ProjectData.from_spreadsheet(at.LIBRARY_PATH+'databook_%s.xlsx' % (a),framework=F)
    #     pset = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH+'progbook_%s.xlsx' % (a),F,D)
    #     for covout in pset.covouts.values():
    #         if sc.isstring(covout.imp_interaction) and covout.imp_interaction.lower().strip() == 'best':
    #             covout.imp_interaction = None
    #     pset.save(at.LIBRARY_PATH+'progbook_%s.xlsx' % (a))


def test_progbook_comments():
    P = at.demo("sir")
    P.load_progbook(testdir / "sir_progbook_comment_test.xlsx")


if __name__ == "__main__":
    test_remove_program()
    test_new_workbook()
    test_save_new_progbook()
    test_progbooks()
