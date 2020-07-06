import os
import numpy as np
import atomica as at


def test_combined_creation():
    tmpdir = at.atomica_path(['tests', 'temp'])

    F = at.ProjectFramework(at.LIBRARY_PATH + 'combined_framework.xlsx')
    pops = {
        'SIR_0-4': {'label': 'SIR 0-4', 'type': 'sir'},
        'SIR_5-14': {'label': 'SIR 5-14', 'type': 'sir'},
        'SIR_15-64': {'label': 'SIR 15-64', 'type': 'sir'},
        'UDT_0-14': {'label': 'UDT 0-14', 'type': 'udt'},
        'UDT_15-64': {'label': 'UDT 15-64', 'type': 'udt'},
    }

    transfers = {
        'aging_sir': {'label': 'Aging SIR', 'type': 'sir'},
        'aging_udt': {'label': 'Aging UDT', 'type': 'udt'},
    }

    D = at.ProjectData.new(framework=F, tvec=[2016, 2017, 2018], pops=pops, transfers=transfers)
    D.save(tmpdir / 'combined_test.xlsx')
    D2 = at.ProjectData.from_spreadsheet(tmpdir / 'combined_test.xlsx', framework=F)
    D2.add_pop('UDT_65+', 'UDT 65+', 'udt')
    D2.add_transfer('incarceration', 'Incarceration', 'sir')
    D2.save(tmpdir / 'combined_test2.xlsx')

    D3 = at.ProjectData.from_spreadsheet(tmpdir / 'combined_test.xlsx', framework=F)  # Load in the original one because it has no missing values
    D3.validate(F)

    P = at.Project(framework=F, databook=tmpdir / 'combined_test.xlsx')

    ps = at.ProgramSet.new('default', tvec=np.arange(2015, 2019), progs=9, project=P)
    ps.save(tmpdir / 'combined_progbook_test.xlsx')

    ps2 = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH + 'combined_progbook.xlsx', project=P)
    ps2.add_program('test', 'test')
    ps2.save(tmpdir / 'combined_added.xlsx')


def test_combined_values():
    P1 = at.demo('sir', do_run=False)
    P1.settings.update_time_vector(start=2016, end=2021)
    R1 = P1.run_sim('default')
    P2 = at.demo('udt', do_run=False)
    P2.settings.update_time_vector(start=2016, end=2021)
    R2 = P2.run_sim('default')
    P3 = at.demo('combined', do_run=False)
    P3.settings.update_time_vector(start=2016, end=2021)
    R3 = P3.run_sim('default')

    # Check SIR values
    assert np.allclose(R1.model.pops[0].get_comp('sus').vals, R3.model.pops[0].get_comp('sus').vals, equal_nan=True)
    assert np.allclose(R1.model.pops[0].get_par('foi').vals, R3.model.pops[0].get_par('foi').vals, equal_nan=True)

    # Check UDT values
    assert np.allclose(R2.model.pops[0].get_comp('undx').vals, R3.model.pops[3].get_comp('undx').vals, equal_nan=True)

    # Check interaction values
    # Work through the interaction calculation between SIR and UDT
    interactions = P3.parsets[0].interactions[1]
    x = {}
    for to_pop in ['UDT_0-14', 'UDT_15-64']:
        x[to_pop] = np.zeros(R3.t.shape)
        for from_pop in ['SIR_0-4', 'SIR_5-14', 'SIR_15-64']:
            x[to_pop] += R3.get_variable('foi', from_pop)[0].vals * interactions[from_pop].ts[to_pop].interpolate(R3.t)
    assert np.allclose(R3.get_variable('sum_foi', 'UDT_0-14')[0].vals, x['UDT_0-14'], equal_nan=True)
    assert np.allclose(R3.get_variable('sum_foi', 'UDT_15-64')[0].vals, x['UDT_15-64'], equal_nan=True)


def test_combined_cascades():
    P = at.demo('combined')
    at.get_cascade_vals(P.results[0], 'sir_cascade')[0]
    udt_cascade = at.get_cascade_vals(P.results[0], 'udt_cascade')[0]

    # Check aggregation is correctly applied
    udt_1pop_cascade = at.get_cascade_vals(P.results[0], 'udt_cascade', pops='UDT_0-14')[0]
    udt_explicit_cascade = at.get_cascade_vals(P.results[0], 'udt_cascade', pops=['UDT_0-14', 'UDT_15-64'])[0]

    assert np.allclose(udt_cascade[0], 2 * udt_1pop_cascade[0], equal_nan=True)
    assert np.allclose(udt_cascade[0], udt_explicit_cascade[0], equal_nan=True)


def test_combined_plots():
    P = at.demo('combined')
    P.results[0].plot()


def test_combined_order():
    testdir = os.path.abspath(os.path.join(os.path.dirname(__file__))) + os.sep  # Must be relative to current file to work with tox
    P = at.Project(framework=testdir / 'test_order_framework.xlsx', databook=testdir / 'test_order_databook.xlsx')
    res = P.results[0]

    # This framework has interdependencies that mean the parameters must be resolved in exact framework order
    assert np.all(np.isfinite(res.get_variable('testpar')[0].vals))


if __name__ == "__main__":
    test_combined_creation()
    # test_combined_values()
    # test_combined_cascades()
    # test_combined_plots()
    # test_combined_order()
