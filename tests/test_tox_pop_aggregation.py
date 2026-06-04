"""
Unit tests for the population-aggregation calculation in ``Model.update_pars``.

Run via the test suite, or directly:

    uv run pytest tests/test_tox_pop_aggregation.py -v
    # or
    uv run python tests/test_tox_pop_aggregation.py

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

Non-square (cross-population-type) tests
-----------------------------------------
When source and target populations belong to different population types, the interaction matrix is
not square: shape ``(n_src, n_tgt, ntime)``.  ``TGT_POP_*`` functions are invalid for cross-type
interactions (see the Population-Types documentation), so only ``SRC_POP_AVG`` and ``SRC_POP_SUM``
are exercised in the rectangular-matrix tests.

The 3-source / 2-target tests use:
* ``Q3``  -- source quantity values (reused from the square tests)
* ``C3``  -- source characteristic sizes (reused)
* ``W32`` -- weight matrix of shape ``(3, 2, 1)``:
    ``[[1, 2], [3, 4], [5, 6]]``  at ``ti = 0``

  After the SRC_POP transpose to shape ``(2, 3)``:
    row 0 (target 0): weights ``[1, 3, 5]``, sum = 9
    row 1 (target 1): weights ``[2, 4, 6]``, sum = 12

  SRC_POP_SUM (no charac):   [1·0.9+3·0.5+5·0.3, 2·0.9+4·0.5+6·0.3] = [3.9, 5.6]
  SRC_POP_AVG (no charac):   [3.9/9, 5.6/12]                         = [13/30, 7/15]
  SRC_POP_SUM (unit+charac): [Σ(C·Q), Σ(C·Q)] = [280, 280]
  SRC_POP_AVG (unit+charac): [Σ(C·Q)/Σ(C), ...] = [7/15, 7/15]
  SRC_POP_SUM (W32+charac):  [Σ(W_col0·C·Q), Σ(W_col1·C·Q)]
                              = [1·100·0.9+3·200·0.5+5·300·0.3,
                                 2·100·0.9+4·200·0.5+6·300·0.3]
                              = [840, 1120]
  SRC_POP_AVG (W32+charac):  [840/2200, 1120/2800] = [21/55, 2/5]

The 1-source / 2-target tests use:
* ``Q1``  -- single source quantity value (reused)
* ``C1``  -- single source characteristic size (reused)
* ``W12`` -- weight matrix of shape ``(1, 2, 1)``:
    ``[[2, 3]]``  at ``ti = 0``

  After the SRC_POP transpose to shape ``(2, 1)``:
    row 0 (target 0): weights ``[2]``, sum = 2
    row 1 (target 1): weights ``[3]``, sum = 3

  With only 1 source population each transposed row has exactly one element,
  so for SRC_POP_AVG the weight always cancels in normalisation — the result is
  always the (optionally charac-weighted then renormalised) source value,
  independent of the interaction weights.

  SRC_POP_SUM (no charac):   [2·0.9, 3·0.9]   = [1.8, 2.7]
  SRC_POP_AVG (no charac):   [0.9, 0.9]        (weight cancels)
  SRC_POP_SUM (unit+charac): [1·100·0.9, same] = [90, 90]
  SRC_POP_AVG (unit+charac): [0.9, 0.9]        (weight·charac cancels)
  SRC_POP_SUM (W12+charac):  [2·100·0.9, 3·100·0.9] = [180, 270]
  SRC_POP_AVG (W12+charac):  [0.9, 0.9]        (weight·charac cancels)
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

# Non-square (3 source, 2 target) interaction weights — shape (n_src, n_tgt, ntime)
# At ti=0: [[1,2],[3,4],[5,6]]; after SRC_POP transpose (2,3): row0=[1,3,5] row1=[2,4,6]
W32 = np.array([[[1.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]]])  # shape (3, 2, 1)

# Non-square (1 source, 2 target) interaction weights — shape (1, 2, ntime)
# At ti=0: [[2, 3]]; after SRC_POP transpose (2,1): each row has one element so AVG weight cancels
W12 = np.array([[[2.0], [3.0]]])  # shape (1, 2, 1)

AGG_FCNS = ["SRC_POP_AVG", "SRC_POP_SUM", "TGT_POP_AVG", "TGT_POP_SUM"]
SRC_AGG_FCNS = ["SRC_POP_AVG", "SRC_POP_SUM"]  # only valid for cross-population-type aggregations


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
def test_3pop_no_weights_no_charac():
    # Case 1: no interaction, no characteristic weighting (hits the no-weighting fast path)
    expected = {
        "SRC_POP_AVG": np.ones(3)*Q3.mean(),
        "SRC_POP_SUM": np.ones(3)*Q3.sum(),
        "TGT_POP_AVG": np.ones(3)*Q3.mean(),
        "TGT_POP_SUM": np.ones(3)*Q3.sum(),
    }
    _run_matrix(3, Q3, None, None, expected, "3pop no weights")


def test_3pop_unit_weights_no_charac():
    # Case 2: all-ones interaction, no characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": np.ones(3)*Q3.mean(),
        "SRC_POP_SUM": np.ones(3)*Q3.sum(),
        "TGT_POP_AVG": np.ones(3)*Q3.mean(),
        "TGT_POP_SUM": np.ones(3)*Q3.sum(),
    }
    _run_matrix(3, Q3, np.ones((3, 3, 1)), None, expected, "3pop unit weights, no charac")


def test_3pop_nonunit_weights_no_charac():
    # Case 3: weight matrix above, no characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": [0.41666666666666663, 0.44666666666666666, 0.4666666666666667],
        "SRC_POP_SUM": [5,6.7,8.4],
        "TGT_POP_AVG": [0.4666666666666667, 0.5266666666666667, 0.5416666666666667],
        "TGT_POP_SUM": [2.8,7.9,13],
    }

    _run_matrix(3, Q3, W3, None, expected, "3pop nonunit weights, no charac")


def test_3pop_unit_weights_charac():
    # Case 4: all-ones interaction, with characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": np.ones(3)*((Q3*C3).sum()/C3.sum()),
        "SRC_POP_SUM": np.ones(3)*((Q3*C3).sum()).sum(),
        "TGT_POP_AVG": np.ones(3)*((Q3*C3).sum()/C3.sum()),
        "TGT_POP_SUM": np.ones(3)*((Q3*C3).sum()).sum(),
    }
    _run_matrix(3, Q3, np.ones((3, 3, 1)), C3, expected, "3pop unit weights + charac")


def test_3pop_nonunit_weights_charac():
    # Case 5: weight matrix above, with characteristic weighting (hits the general n x n path)
    expected = {
        "SRC_POP_AVG": [0.37333333333333335, 0.38888888888888884, 0.4],
        "SRC_POP_SUM": [1120.0, 1400.0, 1680.0],
        "TGT_POP_AVG": [0.4, 0.4375, 0.448],
        "TGT_POP_SUM": [560.0, 1400.0, 2240.0],
    }
    _run_matrix(3, Q3, W3, C3, expected, "3pop nonunit weights + charac")


# =======================================================================================
# 1-population tests
# =======================================================================================
def test_1pop_no_weights():
    # Case 1: no interaction, no characteristic weighting (hits the no-weighting fast path)
    expected = {
        "SRC_POP_AVG": Q1,
        "SRC_POP_SUM": Q1,
        "TGT_POP_AVG": Q1,
        "TGT_POP_SUM": Q1,
    }
    _run_matrix(1, Q1, None, None, expected, "1pop no weights")


def test_1pop_unit_weights_no_charac():
    # Case 2: all-ones 1x1 interaction, no characteristic weighting (hits the 1x1 fast path)
    expected = {
        "SRC_POP_AVG": Q1,
        "SRC_POP_SUM": Q1,
        "TGT_POP_AVG": Q1,
        "TGT_POP_SUM": Q1,
    }
    _run_matrix(1, Q1, np.ones((1, 1, 1)), None, expected, "1pop unit weights, no charac")


def test_1pop_nonunit_weights_no_charac():
    # Case 3: non-unit 1x1 interaction ([[5]]), no characteristic weighting (hits the 1x1 fast path)
    # AVG: the single weight cancels in normalisation -> Q1; SUM: weight * Q1.
    expected = {
        "SRC_POP_AVG": Q1,
        "SRC_POP_SUM": Q1 * W1[0, 0, 0],
        "TGT_POP_AVG": Q1,
        "TGT_POP_SUM": Q1 * W1[0, 0, 0],
    }
    _run_matrix(1, Q1, W1, None, expected, "1pop nonunit weights, no charac")


def test_1pop_unit_weights_charac():
    # Case 4: all-ones 1x1 interaction, with characteristic weighting (hits the 1x1 fast path)
    # AVG: charac cancels in normalisation -> Q1; SUM: charac * Q1 (weight is 1).
    expected = {
        "SRC_POP_AVG": Q1,
        "SRC_POP_SUM": Q1 * C1,
        "TGT_POP_AVG": Q1,
        "TGT_POP_SUM": Q1 * C1,
    }
    _run_matrix(1, Q1, np.ones((1, 1, 1)), C1, expected, "1pop unit weights + charac")


def test_1pop_nonunit_weights_charac():
    # Case 5: non-unit 1x1 interaction ([[5]]), with characteristic weighting (hits the 1x1 fast path)
    # AVG: weight & charac cancel in normalisation -> Q1; SUM: weight * charac * Q1.
    expected = {
        "SRC_POP_AVG": Q1,
        "SRC_POP_SUM": Q1 * W1[0, 0, 0] * C1,
        "TGT_POP_AVG": Q1,
        "TGT_POP_SUM": Q1 * W1[0, 0, 0] * C1,
    }
    _run_matrix(1, Q1, W1, C1, expected, "1pop nonunit weights + charac")


# =======================================================================================
# Non-square (cross-population-type) tests: 3 source populations, 2 target populations
# =======================================================================================
# Per the Population-Types documentation, TGT_POP_* are invalid when source and target
# populations belong to different types.  The interaction matrix has shape (n_src, n_tgt, ntime)
# = (3, 2, 1), which is non-square, so TGT_POP_* would produce a shape mismatch in matmul.
# Only SRC_POP_AVG and SRC_POP_SUM are exercised here.


def run_aggregation_rect(n_src, n_tgt, agg_fcn, quantity, weights=None, charac=None):
    """Run the real Model.update_pars aggregation with n_src source pops and n_tgt target pops.

    :param n_src: number of source (from) populations
    :param n_tgt: number of target (to) populations
    :param agg_fcn: one of SRC_AGG_FCNS
    :param quantity: length-n_src array, source values at ti=0
    :param weights: None or (n_src, n_tgt, ntime) interaction array
    :param charac: None or length-n_src characteristic array (belongs to the source type)
    :return: length-n_tgt array of aggregated parameter values at ti=0
    """
    ti = 0
    m = FakeModel(ntime=1)
    m._t_index = ti

    m._vars_by_pop["src"] = [FakeVar(f"src{p}", [quantity[p]]) for p in range(n_src)]

    if weights is None:
        pop_aggregation = (agg_fcn, "src")
    else:
        m.interactions["inter"] = np.asarray(weights, dtype=float)
        if charac is None:
            pop_aggregation = (agg_fcn, "src", "inter")
        else:
            m._vars_by_pop["charac"] = [FakeVar(f"charac{p}", [charac[p]]) for p in range(n_src)]
            pop_aggregation = (agg_fcn, "src", "inter", "charac")

    m._vars_by_pop["agg"] = [FakeVar(f"agg{p}", [np.nan], pop_aggregation=pop_aggregation) for p in range(n_tgt)]

    Model.update_pars(m)
    return np.array([p[ti] for p in m._vars_by_pop["agg"]])


def _run_matrix_src_only(n_src, n_tgt, quantity, weights, charac, expected, prefix):
    checked = 0
    for fcn in SRC_AGG_FCNS:
        result = run_aggregation_rect(n_src=n_src, n_tgt=n_tgt, agg_fcn=fcn, quantity=quantity, weights=weights, charac=charac)
        print(fcn, result)
        if expected[fcn] is None:
            continue
        exp = np.asarray(expected[fcn], dtype=float)
        label = f"{prefix} [{fcn}]"
        assert result.shape == exp.shape, f"{label}: result shape {result.shape} != expected shape {exp.shape}"
        assert np.allclose(result, exp, rtol=1e-12, atol=1e-12), f"{label}: result {result} != expected {exp}"
        checked += 1
    if checked == 0:
        pytest.skip(f"{prefix}: no expected results specified yet")


def test_3src2tgt_no_weights():
    # Fast path (no interaction matrix): each of the 2 target pops gets mean/sum of all 3 source vals
    expected = {
        "SRC_POP_AVG": np.full(2, Q3.mean()),
        "SRC_POP_SUM": np.full(2, Q3.sum()),
    }
    _run_matrix_src_only(3, 2, Q3, None, None, expected, "3src2tgt no weights")


def test_3src2tgt_unit_weights_no_charac():
    # All-ones (3,2) interaction: same result as the no-weights fast path
    expected = {
        "SRC_POP_AVG": np.full(2, Q3.mean()),
        "SRC_POP_SUM": np.full(2, Q3.sum()),
    }
    _run_matrix_src_only(3, 2, Q3, np.ones((3, 2, 1)), None, expected, "3src2tgt unit weights, no charac")


def test_3src2tgt_nonunit_weights_no_charac():
    # W32 transposed to (2,3): row0=[1,3,5] sum=9, row1=[2,4,6] sum=12
    # SRC_POP_SUM: dot([1,3,5], Q3)=3.9  dot([2,4,6], Q3)=5.6
    # SRC_POP_AVG: 3.9/9=13/30           5.6/12=7/15
    expected = {
        "SRC_POP_AVG": [13 / 30, 7 / 15],
        "SRC_POP_SUM": [3.9, 5.6],
    }
    _run_matrix_src_only(3, 2, Q3, W32, None, expected, "3src2tgt nonunit weights, no charac")


def test_3src2tgt_unit_weights_charac():
    # Unit (3,2) weights * C3 -> each target row = [100, 200, 300], sum=600
    # SRC_POP_AVG: Σ(C3·Q3)/Σ(C3) = 280/600 = 7/15 for both targets
    # SRC_POP_SUM: Σ(C3·Q3) = 280 for both targets
    expected = {
        "SRC_POP_AVG": np.full(2, (Q3 * C3).sum() / C3.sum()),
        "SRC_POP_SUM": np.full(2, (Q3 * C3).sum()),
    }
    _run_matrix_src_only(3, 2, Q3, np.ones((3, 2, 1)), C3, expected, "3src2tgt unit weights + charac")


def test_3src2tgt_nonunit_weights_charac():
    # W32 transposed to (2,3), then multiplied by C3:
    #   target 0: [1*100, 3*200, 5*300] = [100, 600, 1500], sum=2200
    #   target 1: [2*100, 4*200, 6*300] = [200, 800, 1800], sum=2800
    # SRC_POP_SUM: [100·0.9+600·0.5+1500·0.3, 200·0.9+800·0.5+1800·0.3] = [840, 1120]
    # SRC_POP_AVG: [840/2200, 1120/2800] = [21/55, 2/5]
    expected = {
        "SRC_POP_AVG": [21 / 55, 2 / 5],
        "SRC_POP_SUM": [840.0, 1120.0],
    }
    _run_matrix_src_only(3, 2, Q3, W32, C3, expected, "3src2tgt nonunit weights + charac")


# =======================================================================================
# Non-square (cross-population-type) tests: 1 source population, 2 target populations
# =======================================================================================
# shape (1, 2, ntime) misses both fast paths (1x1 requires shape[1]==1 too) and hits the
# general matmul.  With a single source the transposed weight matrix has shape (2, 1), so
# each target row contains exactly one weight — for SRC_POP_AVG that weight is also the row
# norm, so it cancels and the result is always just Q1 regardless of the interaction weights.
# TGT_POP_* would attempt (1, 2) @ (1, 1) and raise a ValueError (shape mismatch).


def test_1src2tgt_no_weights():
    # Fast path: each of the 2 target pops gets mean/sum of the single source value
    expected = {
        "SRC_POP_AVG": np.full(2, Q1[0]),
        "SRC_POP_SUM": np.full(2, Q1[0]),
    }
    _run_matrix_src_only(1, 2, Q1, None, None, expected, "1src2tgt no weights")


def test_1src2tgt_unit_weights_no_charac():
    # All-ones (1, 2) weights: same result as no-weights
    expected = {
        "SRC_POP_AVG": np.full(2, Q1[0]),
        "SRC_POP_SUM": np.full(2, Q1[0]),
    }
    _run_matrix_src_only(1, 2, Q1, np.ones((1, 2, 1)), None, expected, "1src2tgt unit weights, no charac")


def test_1src2tgt_nonunit_weights_no_charac():
    # W12 transposed to (2, 1): row0=[2], row1=[3]; AVG weight cancels; SUM = weight * Q1
    expected = {
        "SRC_POP_AVG": np.full(2, Q1[0]),       # weight cancels in single-element rows
        "SRC_POP_SUM": [W12[0, 0, 0] * Q1[0], W12[0, 1, 0] * Q1[0]],  # [1.8, 2.7]
    }
    _run_matrix_src_only(1, 2, Q1, W12, None, expected, "1src2tgt nonunit weights, no charac")


def test_1src2tgt_unit_weights_charac():
    # Unit (1, 2) weights * C1: each target row = [100]; AVG: 100*Q1/100 = Q1; SUM: 100*Q1
    expected = {
        "SRC_POP_AVG": np.full(2, Q1[0]),        # weight·charac cancels
        "SRC_POP_SUM": np.full(2, C1[0] * Q1[0]),  # [90, 90]
    }
    _run_matrix_src_only(1, 2, Q1, np.ones((1, 2, 1)), C1, expected, "1src2tgt unit weights + charac")


def test_1src2tgt_nonunit_weights_charac():
    # W12 transposed (2, 1) then multiplied by C1: row0=[200], row1=[300]
    # AVG: each row-norm equals the single element, so weight·charac cancels → Q1
    # SUM: [2·100·0.9, 3·100·0.9] = [180, 270]
    expected = {
        "SRC_POP_AVG": np.full(2, Q1[0]),
        "SRC_POP_SUM": [W12[0, 0, 0] * C1[0] * Q1[0], W12[0, 1, 0] * C1[0] * Q1[0]],  # [180, 270]
    }
    _run_matrix_src_only(1, 2, Q1, W12, C1, expected, "1src2tgt nonunit weights + charac")


if __name__ == "__main__":
    test_3pop_no_weights_no_charac()
    test_3pop_unit_weights_no_charac()
    test_3pop_nonunit_weights_no_charac()
    test_3pop_unit_weights_charac()
    test_3pop_nonunit_weights_charac()
    test_1pop_no_weights()
    test_1pop_unit_weights_no_charac()
    test_1pop_nonunit_weights_no_charac()
    test_1pop_unit_weights_charac()
    test_1pop_nonunit_weights_charac()
    test_3src2tgt_no_weights()
    test_3src2tgt_unit_weights_no_charac()
    test_3src2tgt_nonunit_weights_no_charac()
    test_3src2tgt_unit_weights_charac()
    test_3src2tgt_nonunit_weights_charac()
    test_1src2tgt_no_weights()
    test_1src2tgt_unit_weights_no_charac()
    test_1src2tgt_nonunit_weights_no_charac()
    test_1src2tgt_unit_weights_charac()
    test_1src2tgt_nonunit_weights_charac()