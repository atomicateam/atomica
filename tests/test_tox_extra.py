# Test that adding an extra population in the data for plotting is OK

import atomica as at


def test_extra_data_pop():
    testdir = at.parent_dir()

    F_path = testdir / 'framework_sir_dynamic.xlsx'
    D_path = testdir / 'databook_sir_dynamic_extra.xlsx'

    P = at.Project(framework=F_path, databook=D_path, do_run=True)

    d = at.PlotData(P.results[0], 'sus')
    at.plot_series(d, data=P.data)

    d.series[0].data_pop = 'national'
    at.plot_series(d, data=P.data)


if __name__ == '__main__':
    test_extra_data_pop()
