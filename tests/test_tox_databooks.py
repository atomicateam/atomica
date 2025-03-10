# This script tests some databook IO operations

import atomica as at
from atomica.excel import transfer_comments
import numpy as np
from atomica import ProjectFramework, Project, ProjectData
import sciris as sc

testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_databooks():

    F = ProjectFramework(at.LIBRARY_PATH / "tb_framework.xlsx")
    F.save(tmpdir / "f_blug.xlsx")

    # Copy a databook by loading and saving it
    data = ProjectData.from_spreadsheet(at.LIBRARY_PATH / "tb_databook.xlsx", F)
    data.save(tmpdir / "d_blug.xlsx")

    # Copy comments, using lower-level Spreadsheet object (for in-memory file operations)
    original_workbook = sc.Spreadsheet(at.LIBRARY_PATH / "tb_databook.xlsx")
    new_workbook = data.to_spreadsheet()  # This is a sc.Spreadsheet that can be stored in the FE database
    transfer_comments(new_workbook, original_workbook)
    new_workbook.save(tmpdir / "d_blug_formatted.xlsx")

    # Run the copied databook
    P = Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=tmpdir / "d_blug.xlsx", make_default_parset=True, do_run=True)
    d = at.PlotData(P.results["parset_default"], pops="0-4")
    at.plot_series(d, plot_type="stacked")  # This should look like the usual Optima-TB result

    # Change the time axis
    d2 = sc.dcp(data)
    d2.change_tvec(np.arange(2000, 2017, 0.5))
    d2.transfers[0].comment = "Test comment"
    d2.save(tmpdir / "d_blug_halfyear.xlsx")

    # Run the half-year databook
    P = Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=tmpdir / "d_blug_halfyear.xlsx", make_default_parset=True, do_run=True)
    d = at.PlotData(P.results["parset_default"], pops="0-4")
    at.plot_series(d, plot_type="stacked")  # This should look like the usual Optima-TB result

    # Change the pops and run it
    data = ProjectData.from_spreadsheet(at.LIBRARY_PATH / "tb_databook.xlsx", F)
    data.rename_pop("0-4", "0-3", "Gen 0-3")
    data.rename_transfer("age", "age_up", "Age Up")
    data.save(tmpdir / "d_blug_renamed.xlsx")
    P = Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=tmpdir / "d_blug_renamed.xlsx", make_default_parset=True, do_run=True)
    d = at.PlotData(P.results["parset_default"], pops="0-3")
    at.plot_series(d, plot_type="stacked")  # This should look like the usual Optima-TB result

    # Remove a key pop
    d2 = sc.dcp(data)
    d2.remove_pop("Prisoners")
    d2.save(tmpdir / "d_blug_nopris.xlsx")

    # Remove a transfer, add an interaction, add a pop
    d2.remove_transfer("inc")
    d2.add_interaction("d_ctc", "New interpop")
    d2.add_pop("asdf", "The ASDF pop")
    d2.save(tmpdir / "d_blug_newpop.xlsx")

    # Make a brand new databook
    d2 = ProjectData.new(F, np.arange(2000, 2017), pops=2, transfers=4)
    d2.save(tmpdir / "d_blug_blank.xlsx")

    # Make a blank databook with the same pops and transfers from the old one
    pops = sc.odict()
    for pop, val in data.pops.items():
        pops[pop] = val["label"]

    transfers = sc.odict()
    for transfer in data.transfers:
        transfers[transfer.code_name] = transfer.full_name

    d2 = ProjectData.new(F, np.arange(2000, 2017), pops=pops, transfers=transfers)
    d2.save(tmpdir / "d_cleared.xlsx")

    # Modify incomplete databook
    d2 = ProjectData.from_spreadsheet(tmpdir / "d_blug_blank.xlsx", F)
    d2.add_pop("asdf", "The ASDF pop")
    d2.add_interaction("d_ctc", "New interpop")
    d2.save(tmpdir / "d_blug_blank_modified.xlsx")

    # Test writing out a databook with uncertainty values
    data = ProjectData.from_spreadsheet(at.LIBRARY_PATH / "tb_databook.xlsx", F)
    data.tdve["alive"].ts[0].sigma = 100

    # Check stripping uncertainty values
    for tdve in data.tdve.values():
        tdve.write_uncertainty = True  # Force writing uncertainty
    data.save(tmpdir / "d_blug_uncertainty.xlsx")  # Every table has uncertainty - this is the default

    # Check stripping uncertainty values
    for tdve in data.tdve.values():
        tdve.write_uncertainty = False
    data.save(tmpdir / "d_blug_uncertainty_stripped.xlsx")  # No tables have uncertainty

    # Check the values get read in correctly
    d3 = at.ProjectData.from_spreadsheet(tmpdir / "d_blug_uncertainty.xlsx", F)
    assert d3.tdve["alive"].ts[0].sigma == 100
    d3 = at.ProjectData.from_spreadsheet(tmpdir / "d_blug_uncertainty_stripped.xlsx", F)
    assert d3.tdve["alive"].ts[0].sigma is None


def test_mixed_years_1():
    F = ProjectFramework(at.LIBRARY_PATH / "sir_framework.xlsx")

    D = at.ProjectData.from_spreadsheet(testdir / "test_databook_mixed_years_1.xlsx", framework=F)
    assert 2020 in D.tvec  # This should get picked up from the second table
    D.add_interaction("d_ctc", "New interpop")
    D.save(tmpdir / "test_databook_mixed_years_1.xlsx")


def test_mixed_years_2():
    F = ProjectFramework(testdir / "test_no_compartment_framework.xlsx")
    D = at.ProjectData.from_spreadsheet(testdir / "test_no_compartment_databook_mixed.xlsx", framework=F)
    assert len(D.tvec) == 0
    D.add_interaction("d_ctc", "New interpop")
    D.save(tmpdir / "test_databook_mixed_years_2a.xlsx")
    D = at.ProjectData.from_spreadsheet(tmpdir / "test_databook_mixed_years_2a.xlsx", framework=F)
    assert len(D.tvec) == 0

    D = at.ProjectData.from_spreadsheet(testdir / "test_no_compartment_databook.xlsx", framework=F)
    D.add_interaction("d_ctc", "New interpop")
    D.save(tmpdir / "test_databook_mixed_years_2b.xlsx")
    D = at.ProjectData.from_spreadsheet(tmpdir / "test_databook_mixed_years_2b.xlsx", framework=F)
    assert len(D.tvec) == 1


def test_databook_comments():
    F = ProjectFramework(at.LIBRARY_PATH / "sir_framework.xlsx")
    D = at.ProjectData.from_spreadsheet(testdir / "sir_databook_comment_test.xlsx", framework=F)
    assert D.get_ts("sus", "Children 0-4").get(2000) == 1  # Should not overwrite existing value
    assert D.get_ts("age", ("Children 0-4", "Children 5-14")).get(2004) == 14  # Should not overwrite existing value
    assert D.get_ts("transfer_1", ("Children 0-4", "Adults 15-64")).get(2000) == 10  # Should not overwrite existing value
    assert D.get_ts("recrate", "Children 0-4").get(2000) == 0.5
    assert D.get_ts("infdeath", "Children 0-4").get(2000) == 0.6
    assert D.transfers[0].attributes["Extra attribute"] == "value"


def test_databook_all():

    F = ProjectFramework(at.LIBRARY_PATH / "sir_framework.xlsx")
    # D = at.ProjectData.new(framework=F, tvec=np.arange(2020,2023),pops=4,transfers=1)
    # D.save(testdir / "sir_databook_all.xlsx")
    D = at.ProjectData.from_spreadsheet(testdir / "sir_databook_all.xlsx", framework=F)

    P = at.Project(framework=F, databook=D, do_run=False)
    P.data.save(tmpdir / "databook_all_test.xlsx")  # Test saving it back
    res = P.run_sim()

    assert len(P.data.tdve["sus"].ts) == 1
    assert len(P.parsets[0].get_par("sus").ts) == 4
    assert len(P.parsets[0].get_par("sus").y_factor) == 4

    # Check all populations have the same susceptible
    assert np.isclose(res.get_variable("sus", "pop_0")[0].vals[0], 100)
    assert np.isclose(res.get_variable("sus", "pop_1")[0].vals[0], 100)
    assert np.isclose(res.get_variable("sus", "pop_2")[0].vals[0], 100)
    assert np.isclose(res.get_variable("sus", "pop_3")[0].vals[0], 100)

    # Check prevalence calculation - 50% prevalence in all populations
    # and 100 susceptible, with pop sizes of 200, 300, 400, 500 should give
    # different values for the inf and rec compartment sizes
    assert np.isclose(res.get_variable("inf", "pop_0")[0].vals[0], 100)
    assert np.isclose(res.get_variable("inf", "pop_1")[0].vals[0], 30)
    assert np.isclose(res.get_variable("inf", "pop_2")[0].vals[0], 200)
    assert np.isclose(res.get_variable("inf", "pop_3")[0].vals[0], 250)

    assert np.isclose(res.get_variable("rec", "pop_0")[0].vals[0], 0)
    assert np.isclose(res.get_variable("rec", "pop_1")[0].vals[0], 170)
    assert np.isclose(res.get_variable("rec", "pop_2")[0].vals[0], 100)
    assert np.isclose(res.get_variable("rec", "pop_3")[0].vals[0], 150)

    d = at.PlotData(res, outputs=["sus", "ch_prev", "ch_all"], project=P)
    at.plot_series(d, axis="pops", data=P.data)


def test_databook_default_all():
    F = at.ProjectFramework(testdir / "sir_framework_default_all.xlsx")
    D = at.ProjectData.new(F, np.arange(2000, 2005), pops=4, transfers=1)
    D.save(tmpdir / "databook_default_all_test.xlsx")  # Test saving it back

    D.add_pop("new", "new")
    assert list(D.tdve["sus"].ts.keys()) == ["pop_0", "pop_1", "pop_2", "pop_3", "new"]
    assert list(D.tdve["ch_prev"].ts.keys()) == ["All"]

    D.tdve["contacts"].ts["pop_0"] = D.tdve["contacts"].ts["All"]
    del D.tdve["contacts"].ts["All"]
    D.add_pop("new2", "new2")
    assert list(D.tdve["ch_prev"].ts.keys()) == ["All"]
    assert list(D.tdve["contacts"].ts.keys()) == ["pop_0", "new2"]
    D.save(tmpdir / "databook_default_all_test_2.xlsx")  # Test saving it back


if __name__ == "__main__":
    # test_mixed_years_2()
    # test_mixed_years_1()
    # test_databooks()
    # test_databook_comments()
    # test_databook_all()
    test_databook_default_all()
