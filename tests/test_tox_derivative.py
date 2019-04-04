# Test that parameter derivatives work
# Indirectly test that frameworks with no compartments work

import numpy as np
import atomica as at

def test_derivative():

    testdir = at.atomica_path(['tests'])

    F = at.ProjectFramework(testdir + "framework_derivative_test.xlsx")
    D = at.ProjectData.new(F,np.arange(2000,2010),pops={'mosquitos':'Mosquitos'},transfers=0)

    P = at.Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=D.to_spreadsheet(), make_default_parset=True, do_run=True)

    dm_prev = P.results[0].get_variable('dm_prev', 'mosquitos')[0]
    m_prev = P.results[0].get_variable('m_prev', 'mosquitos')[0]

    assert np.allclose(dm_prev.vals[m_prev.t==2000], 0.1, equal_nan=True)
    assert np.allclose(dm_prev.vals[m_prev.t==2010], 0.1, equal_nan=True)

    assert np.allclose(m_prev.vals[m_prev.t==2000], 0.5, equal_nan=True)
    assert np.allclose(m_prev.vals[m_prev.t==2002.5], 0.75, equal_nan=True)
    assert np.allclose(m_prev.vals[m_prev.t==2005], 1.0, equal_nan=True)
    assert np.allclose(m_prev.vals[m_prev.t==2010], 1.0, equal_nan=True)

    print('Test successfully completed')

if __name__ == '__main__':
    test_derivative()