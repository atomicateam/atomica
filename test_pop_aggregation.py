"""
Unit tests for the population-aggregation calculation in ``Model.update_pars``.

This is intentionally NOT part of the committed test suite. Run it directly:

    uv run python test_pop_aggregation.py
    # or
    uv run pytest test_pop_aggregation.py -v

It exercises the *real* (current) ``Model.update_pars`` aggregation block by driving it with a
lightweight fake ``self`` that provides only the attributes the aggregation block touches (no
project/databook is loaded). Because it calls the actual ``Model.update_pars``, the test reflects
exactly the code that ships.

Fixed inputs (single time point, ``ti = 0``)
-------------------------------------------
* quantity being aggregated : ``[0.9, 0.5, 3]``        (1-pop tests use ``[0.9]``)
* characteristic size        : ``[100, 200, 300]``      (1-pop tests use ``[100]``)
* interaction weight matrix  : ``np.arange(1, 10).reshape((3, 3, 1))``  (1-pop tests use a 1x1 [[5]])

Case matrix (run for 1 population and 3 populations, and for all four aggregation functions):

  1. No interaction weights, no characteristic weighting       -> len(pop_aggregation) == 2
  2. Interaction weights all 1, no characteristic weighting    -> len == 3, all-ones matrix
  3. Interaction weights != 1, no characteristic weighting     -> len == 3, the matrix above
  4. Interaction weights all 1, with characteristic weighting  -> len == 4, all-ones matrix
  5. Interaction weights != 1, with characteristic weighting   -> len == 4, the matrix above

The ``expected`` result for each case is to be filled in by hand (an array with one entry per
population). Until specified, the corresponding assertion is skipped.
"""

import sys
import numpy as np
import pytest
from atomica.model import Model


# --- Fixed inputs ----------------------------------------------------------------------
Q3 = np.array([0.9, 0.5, 0.3])                          # quantity being aggregated (3 pops)
C3 = np.array([100.0, 200.0, 300.0])                    # characteristic size (3 pops)
W3 = np.arange(1, 10).reshape((3, 3, 1)).astype(float)  # interaction weights (3 x 3 x ntime)

Q1 = np.array([0.9])                                    # quantity being aggregated (1 pop)
C1 = np.array([100.0])                                  # characteristic size (1 pop)
W1 = np.array([5.0]).reshape((1, 1, 1))                 # non-unit interaction weight (1 x 1 x ntime)

AGG_FCNS = ["SRC_POP_AVG", "SRC_POP_SUM", "TGT_POP_AVG", "TGT_POP_SUM"]


# --- Minimal fakes that satisfy the attributes Model.update_pars touches ----------------
class FakeVar:
    """Stands in for a Parameter/Variable: indexable storage plus the few attrs used."""

    def __init__(self, name, vals, pop_aggregation=None, scale_factor=1.0):
        self.name = name
        self.vals = np.asarray(vals, dtype=float)
        self.pop_aggregation = pop_aggregation
        self.scale_factor = scale_factor
        self.skip_function = None
        self._is_dynamic = False
        self.derivative = False

    def __getitem__(self, ti):
        return self.vals[ti]

    def __setitem__(self, ti, v):
        self.vals[ti] = v

    def update(self, ti):  # never called (_is_dynamic is False)
        raise AssertionError("update() should not be called in this harness")

    def constrain(self, ti):  # no limiting range in this harness
        pass


class FakeModel:
    """Carries only what Model.update_pars reads (programs are disabled)."""

    def __init__(self, ntime):
        self._t_index = None
        self.t = np.linspace(2020.0, 2020.0 + (ntime - 1), ntime)
        self.dt = 1.0
        self.programs_active = False
        self.program_instructions = None
        self._exec_order = {"characs": [], "dynamic_pars": ["agg"]}
        self._vars_by_pop = {}
        self.interactions = {}


# --- Harness ---------------------------------------------------------------------------
def run_aggregation(npop, agg_fcn, quantity, weights=None, charac=None):
    """Run the real Model.update_pars aggregation for one configuration.

    :param npop: number of populations
    :param agg_fcn: one of AGG_FCNS
    :param quantity: length-npop array, the values being aggregated (at ti=0)
    :param weights: None for no interaction, else an (npop, npop, ntime) array
    :param charac: None for no characteristic weighting, else a length-npop array
    :return: length-npop array of the aggregated parameter values at ti=0
    """
    ti = 0
    m = FakeModel(ntime=1)
    m._t_index = ti

    m._vars_by_pop["src"] = [FakeVar(f"src{p}", [quantity[p]]) for p in range(npop)]

    if weights is None:
        pop_aggregation = (agg_fcn, "src")
    else:
        m.interactions["inter"] = np.asarray(weights, dtype=float)
        if charac is None:
            pop_aggregation = (agg_fcn, "src", "inter")
        else:
            m._vars_by_pop["charac"] = [FakeVar(f"charac{p}", [charac[p]]) for p in range(npop)]
            pop_aggregation = (agg_fcn, "src", "inter", "charac")

    # Target parameters initialised to NaN so an untouched parameter is detectable.
    m._vars_by_pop["agg"] = [FakeVar(f"agg{p}", [np.nan], pop_aggregation=pop_aggregation) for p in range(npop)]

    Model.update_pars(m)
    return np.array([p[ti] for p in m._vars_by_pop["agg"]])


def _run_matrix(npop, quantity, weights, charac, expected, prefix):
    checked = 0
    for fcn in AGG_FCNS:
        result = run_aggregation(npop=npop, agg_fcn=fcn, quantity=quantity, weights=weights, charac=charac)
        print(fcn, result)
        if expected[fcn] is None:
            continue  # expected result not yet specified for this aggregation function
        exp = np.asarray(expected[fcn], dtype=float)
        label = f"{prefix} [{fcn}]"
        assert result.shape == exp.shape, f"{label}: result shape {result.shape} != expected shape {exp.shape}"
        assert np.allclose(result, exp, rtol=1e-12, atol=1e-12), f"{label}: result {result} != expected {exp}"
        checked += 1
    if checked == 0:
        pytest.skip(f"{prefix}: no expected results specified yet")


# =======================================================================================
# 3-population tests
# =======================================================================================
def test_3pop_no_weights():
    # Case 1: no interaction, no characteristic weighting (hits the no-weighting fast path)
    expected = {
        "SRC_POP_AVG": np.ones(3)*Q3.mean(),  # TODO: np.array([...])
        "SRC_POP_SUM": np.ones(3)*Q3.sum(),  # TODO
        "TGT_POP_AVG": np.ones(3)*Q3.mean(),  # TODO
        "TGT_POP_SUM": np.ones(3)*Q3.sum(),  # TODO
    }
    _run_matrix(3, Q3, None, None, expected, "3pop no weights")


def test_3pop_unit_weights_no_charac():
    # Case 2: all-ones interaction, no characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(3, Q3, np.ones((3, 3, 1)), None, expected, "3pop unit weights, no charac")


def test_3pop_nonunit_weights_no_charac():
    # Case 3: weight matrix above, no characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(3, Q3, W3, None, expected, "3pop nonunit weights, no charac")


def test_3pop_unit_weights_charac():
    # Case 4: all-ones interaction, with characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": np.ones(3)*(Q3*C3/C3.sum()).mean(),  # TODO
        "SRC_POP_SUM": np.ones(3)*(Q3*C3/C3.sum()).sum(),  # TODO
        "TGT_POP_AVG": np.ones(3)*(Q3*C3/C3.sum()).mean(),  # TODO
        "TGT_POP_SUM": np.ones(3)*(Q3*C3/C3.sum()).sum(),  # TODO
    }
    _run_matrix(3, Q3, np.ones((3, 3, 1)), C3, expected, "3pop unit weights + charac")


def test_3pop_nonunit_weights_charac():
    # Case 5: weight matrix above, with characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(3, Q3, W3, C3, expected, "3pop nonunit weights + charac")


# =======================================================================================
# 1-population tests
# =======================================================================================
def test_1pop_no_weights():
    # Case 1: no interaction, no characteristic weighting (hits the no-weighting fast path)
    expected = {
        "SRC_POP_AVG": np.ones(1)*Q1.sum(),  # TODO
        "SRC_POP_SUM": np.ones(1)*Q1.sum(),  # TODO
        "TGT_POP_AVG": np.ones(1)*Q1.sum(),  # TODO
        "TGT_POP_SUM": np.ones(1)*Q1.sum(),  # TODO
    }
    _run_matrix(1, Q1, None, None, expected, "1pop no weights")


def test_1pop_unit_weights_no_charac():
    # Case 2: all-ones 1x1 interaction, no characteristic weighting (hits the 1x1 fast path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(1, Q1, np.ones((1, 1, 1)), None, expected, "1pop unit weights, no charac")


def test_1pop_nonunit_weights_no_charac():
    # Case 3: non-unit 1x1 interaction ([[5]]), no characteristic weighting (hits the 1x1 fast path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(1, Q1, W1, None, expected, "1pop nonunit weights, no charac")


def test_1pop_unit_weights_charac():
    # Case 4: all-ones 1x1 interaction, with characteristic weighting (hits the 1x1 fast path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(1, Q1, np.ones((1, 1, 1)), C1, expected, "1pop unit weights + charac")


def test_1pop_nonunit_weights_charac():
    # Case 5: non-unit 1x1 interaction ([[5]]), with characteristic weighting (hits the 1x1 fast path)
    expected = {
        "SRC_POP_AVG": None,  # TODO
        "SRC_POP_SUM": None,  # TODO
        "TGT_POP_AVG": None,  # TODO
        "TGT_POP_SUM": None,  # TODO
    }
    _run_matrix(1, Q1, W1, C1, expected, "1pop nonunit weights + charac")


if __name__ == "__main__":
    # test_3pop_no_weights()
    # test_3pop_unit_weights_no_charac()
    # test_3pop_nonunit_weights_no_charac()
    test_3pop_unit_weights_charac()
    # test_3pop_nonunit_weights_charac()
    # test_1pop_no_weights()
    # test_1pop_unit_weights_no_charac()
    # test_1pop_nonunit_weights_no_charac()
    # test_1pop_unit_weights_charac()
    # test_1pop_nonunit_weights_charac()