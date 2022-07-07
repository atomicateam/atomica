import atomica as at
import numpy as np
import os

testdir = at.parent_dir()  # Must be relative to current file to work with tox


def test_program_coverage_calculation():

    # F = at.ProjectFramework(testdir+'test_program_calc_framework.xlsx')
    # D = at.ProjectData.new(F, tvec=[2019],pops=1, transfers=0)
    # D.save(testdir+'test_program_calc_databook.xlsx')
    P = at.Project(framework=testdir / "test_program_calc_framework.xlsx", databook=testdir / "test_program_calc_databook.xlsx", do_run=False)

    # ps = at.ProgramSet.new(project=P,progs=3,tvec=[2019])
    # ps.save(testdir+'test_program_calc_progbook.xlsx')
    P.load_progbook(testdir / "test_program_calc_progbook.xlsx")
    P.settings.update_time_vector(start=2019, end=2020, dt=0.25)

    ins = at.ProgramInstructions(start_year=2019)
    res = P.run_sim(parset=0, progset=0, progset_instructions=ins)

    # Check the resulting calculations
    assert res.get_variable("txrate1")[0].vals[0] == 0.8  # At this timestep, should have ANNUALIZED probability of 0.8
    assert res.get_variable("txrate2")[0].vals[0] == 80  # At this timestep, should have ANNUALIZED flow rate of 80

    assert res.get_variable("txrate1:flow")[0].vals[0] == 20  # At this timestep, should have timestep flow of 20
    assert res.get_variable("txrate2:flow")[0].vals[0] == 20  # At this timestep, should have timestep flow of 20

    # With 80 people eligible, funding to cover 20 people at this timestep, the coverage should be 25%
    # and we should continue to move 20 people. The annualized probability is now 1
    assert res.get_variable("txrate1")[0].vals[1] == 1  # At this timestep, should have ANNUALIZED probability of 1
    assert res.get_variable("txrate2")[0].vals[1] == 80  # At this timestep, should have ANNUALIZED flow rate of 80

    assert res.get_variable("txrate1:flow")[0].vals[1] == 20  # At this timestep, should have timestep flow of 20
    assert res.get_variable("txrate2:flow")[0].vals[1] == 20  # At this timestep, should have timestep flow of 20

    assert res.get_variable("prop_art")[0].vals[0] == 0.5  # Parameter value should correspond to 50% coverage

    # Test applying an overwrite
    ins2 = at.ProgramInstructions(start_year=2019, coverage={"tx_prob": 0.5, "tx_num": 0.5, "art": 0.4, "tx_cont": 0.0})
    res2 = P.run_sim(parset=0, progset=0, progset_instructions=ins2)

    assert res2.get_variable("txrate1")[0].vals[0] == 0.5  # At this timestep, should have ANNUALIZED probability of 0.5
    assert res2.get_variable("txrate2")[0].vals[0] == 50  # At this timestep, should have ANNUALIZED flow corresponding to 50% coverage i.e. 50 people

    assert res2.get_variable("txrate1:flow")[0].vals[0] == 12.5
    assert res2.get_variable("txrate2:flow")[0].vals[0] == 12.5

    # Actual flow rates should be the same regardless of whether the parameter was in number or probability units
    assert np.all(res2.get_variable("txrate1:flow")[0].vals == res2.get_variable("txrate2:flow")[0].vals)

    # Unlike with spending, the coverage remains fixed. Thus with 87.5 people eligible and a TIMESTEP coverage of 50/4=12.5% we have
    # a timestep number transferred of 10.9375. The parameter probability remains 0.5. For the number parameter, we have a timestep
    # coverage of 0.125 which gets multiplied by the parameter source popsize to get the parameter value. The source popsize is
    # now 87.5 so the parameter value is 87.5*0.125/0.25=43.75
    assert res2.get_variable("txrate1")[0].vals[1] == 0.5  # At this timestep, should have ANNUALIZED probability of 0.5
    assert res2.get_variable("txrate2")[0].vals[1] == 43.75  # At this timestep, should have ANNUALIZED flow corresponding to 50% coverage i.e. 50 people

    assert res2.get_variable("txrate1:flow")[0].vals[1] == 10.9375
    assert res2.get_variable("txrate2:flow")[0].vals[1] == 10.9375

    # Actual flow rates should be the same regardless of whether the parameter was in number or probability units
    assert np.all(res2.get_variable("txrate1:flow")[0].vals == res2.get_variable("txrate2:flow")[0].vals)

    assert res2.get_variable("prop_art")[0].vals[0] == 0.4  # Parameter value should correspond to 40% coverage

    # Coverage overwrite for continuous programs

    # Test if a continuous coverage program applies correctly - this should _not_ have a dt adjusted probability or number
    # Note that coverage that is emitted by `ProgramSet.get_prop_coverage` is
    ins3 = at.ProgramInstructions(start_year=2019, coverage={"tx_prob": 0.0, "tx_num": 0.0, "art": 0.4, "tx_cont": 1.0})
    res3 = P.run_sim(parset=0, progset=0, progset_instructions=ins3)

    assert res3.get_variable("txrate1")[0].vals[0] == 2.0  # At this timestep, should have ANNUALIZED probability of 2.0 (100% of coverage with an effect of 0.5)
    assert res3.get_variable("txrate2")[0].vals[0] == 200  # At this timestep, should have ANNUALIZED flow corresponding to 100% coverage at 0.5 effect i.e. 200 people/year

    assert res3.get_variable("txrate1:flow")[0].vals[0] == 50
    assert res3.get_variable("txrate2:flow")[0].vals[0] == 50

    # Actual flow rates should be the same regardless of whether the parameter was in number or probability units
    assert np.all(res3.get_variable("txrate1:flow")[0].vals == res3.get_variable("txrate2:flow")[0].vals)

    # Test the combination of continuous coverage and one-off coverage programs
    ins4 = at.ProgramInstructions(start_year=2019, coverage={"tx_prob": 0.5, "tx_num": 0.5, "art": 0.4, "tx_cont": 1.0})
    res4 = P.run_sim(parset=0, progset=0, progset_instructions=ins4)

    # 100% timestep coverage of the continuous program, with 0.5 effect
    # 50% annual coverage = 12.5% timestep coverage of tx_prob with 1.0 effect
    # Equates to 1*0.125+0.5*(1-0.125)=0.5625/timestep. Or 2.25 annually
    annual_rate = (1 * 0.125 + 0.5 * (1 - 0.125)) * 4
    assert res4.get_variable("txrate1")[0].vals[0] == annual_rate
    assert res4.get_variable("txrate2")[0].vals[0] == annual_rate * 100  # At this timestep, should have ANNUALIZED flow corresponding to the above

    assert res4.get_variable("txrate1:flow")[0].vals[0] == annual_rate * 100 / 4
    assert res4.get_variable("txrate2:flow")[0].vals[0] == annual_rate * 100 / 4

    # Actual flow rates should be the same regardless of whether the parameter was in number or probability units
    assert np.all(res4.get_variable("txrate1:flow")[0].vals == res4.get_variable("txrate2:flow")[0].vals)


#
# def test_no_program_progset():
#
#     P = at.demo('sir', do_run=False)
#
#     tvec = P.settings.tvec
#     dt = P.settings.sim_dt
#     instructions = at.ProgramInstructions(start_year=2020)
#
#
#     ps1 = P.progsets[0]
#     ps2 = at.ProgramSet(framework=P.framework, data=P.data)
#
#     capacities1 = ps1.get_capacities(tvec, dt, instructions)
#     capacities2 = ps2.get_capacities(tvec, dt, instructions)
#
#     def get_prop_coverage(self, tvec, dt, capacities: dict, num_eligible: dict, instructions=None) -> dict:
#
#
#     coverage1 = ps1.get_coverage(tvec, dt, capacities1, )
#     ps.to_spreadsheet() # Check that a spreadsheet can be produced
#     ps
#
#
#     ps1 = P.progsets[0]
#   _get_code_name()    add_pop()           remove_par()
#   _normalize_inpu...  add_program()       remove_pop()
#   _read_effects()     copy()              remove_program()
#   _read_spending()    from_spreadsheet()  sample()
#   _read_targeting()   get_alloc()         save()
#   _write_effects()    get_capacities()    to_spreadsheet()
#   _write_spending()   get_outcomes()      to_workbook()
#   _write_targeting()  get_prop_covera...  validate()
#   add_comp()          new()               add_par()
#   remove_comp()
#
# TypeError: get_prop_coverage() missing 4 required positional arguments: 'tvec', 'dt', 'capacities', and 'num_eligible'


if __name__ == "__main__":
    test_program_coverage_calculation()
    # test_no_program_progset()
