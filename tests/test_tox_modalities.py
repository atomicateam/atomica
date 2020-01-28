# Simple modalities test
import atomica as au
from atomica.programs import Covout
import sciris as sc
import numpy as np


def test_modalities():

    old_settings = np.seterr(all='raise')

    def run_test(coverage, outcomes, baseline, expected=None, imp_interaction=None):
        # cov - 1D vector of coverages
        # outcomes - 1D vector of outcomes
        # baseline - The baseline value
        # expected - target values for [additive, random, nested]
        if expected is None:
            expected = np.full((len(coverage),), np.nan)

        progs = ['P%d' % (x) for x in range(0, len(coverage))]
        coverage = {prog: [val] for prog, val in zip(progs, coverage)}

        covout = Covout(par='testpar',
                        pop='testpop',
                        cov_interaction='additive',
                        imp_interaction=imp_interaction,
                        baseline=baseline,
                        progs={prog: val for prog, val in zip(progs, outcomes)}
                        )

        covout.cov_interaction = 'additive'
        additive = covout.get_outcome(prop_covered=coverage)
        print('Additive = %.4f, Target = %.4f' % (additive, expected[0]))
        if np.isfinite(expected[0]):
            assert np.isclose(additive, expected[0], 1e-4)

        covout.cov_interaction = 'random'
        random = covout.get_outcome(prop_covered=coverage)
        print('Random = %.4f, Target = %.4f' % (random, expected[1]))
        if np.isfinite(expected[1]):
            assert np.isclose(random, expected[1], 1e-4)

        covout.cov_interaction = 'nested'
        nested = covout.get_outcome(prop_covered=coverage)
        print('Nested = %.4f, Target = %.4f' % (nested, expected[2]))
        if np.isfinite(expected[2]):
            assert np.isclose(nested, expected[2], 1e-4)

        return (additive, random, nested)  # Return outcomes

    # Test cases where we have an externally computed result
    # These should both run, and return a specific value
    run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, [0.6125, 0.56308, 0.45])  # Coverages below 1.0
    run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, [0.6125, 0.56308, 0.45])  # Coverages add to exactly 1.0
    run_test([0.2, 0.15, 0.3, 0.1], [50, 40, 20, 80], 5)  # Coverages all different, add to < 1
    run_test([0.244945, 0.022795, 0.056632], [0.8, 0.9, 0.4], 0.3, [0.4418126, 0.4375362, 0.4247518])  # 3 program test from HIV
    run_test([0.3, 0.2, 0.1, 0.05], [0.8, 0.9, 0.4, 0.35], 0.3, [0.5825, 0.54686, 0.47])
    run_test([1., 1., 1., 1.], [0.8, 0.9, 0.4, 0.35], 0.3, [0.9, 0.9, 0.9])  # Tiebreaking case where all coverages are the same, and 1.0
    run_test([1., 1., 1., 1.], [0.5, 0.5, 0.5, 0.5], 0.3, [0.5, 0.5, 0.5])  # Tiebreaking case where all outcomes and coverages are the same
    run_test([0.1, 0.0, 0.2, 0.3], [0.5, 0.5, 0.5, 0.5], 0.3, [0.42, 0.3992, 0.36])  # One of them has zero coverage, total coverage < 1
    run_test([0.6, 0.0, 0.2, 0.3], [0.5, 0.5, 0.5, 0.5], 0.3, [0.5, 0.4552, 0.42])  # One of them has zero coverage, total coverage > 1
    run_test([0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.5, 0.5], 0.3, [0.3, 0.3, 0.3])  # All of them have zero coverage
    run_test([0.3, 0.3, 0.3, 0.3], [0.8, 0.9, 0.4, 0.35], 0.3, [0.665, 0.604845, 0.48])  # Coverages all same, and sum to > 1

    # Different, duplicate,identical,includes 1
    # - Coverages add to <        [0.05,0.1,0.15,0.2],[0.05,0.15,0.15,0.2],[0.2,0.2,0.2,0.2]
    # - Coverages exactly 1       [0.1,0.2,0.3,0.4]  ,[0.1,0.2,0.2,0.5] , [0.3,0.3,0.3,0.3], [0,0,0,1]
    # - Coverages > 1             [0.2,0.3,0.4,0.5]  ,[0.1,0.15,0.2,0.25], [0.4,0.4,0.4,0.4], [1,1,1,1]

    # Next, check exhaustively for numerical edge cases. There are too many combinations to check explicitly
    # so just run them to check that an error does not occur
    coverages = [[0.05, 0.1, 0.15, 0.2], [0.05, 0.15, 0.15, 0.2], [0.2, 0.2, 0.2, 0.2], [0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.2, 0.5], [0.3, 0.3, 0.3, 0.3], [0., 0., 0., 1.], [0.2, 0.3, 0.4, 0.5], [0.1, 0.15, 0.2, 0.25], [0.4, 0.4, 0.4, 0.4], [1., 1., 1., 1.]]
    outcomes = [[0.05, 0.1, 0.15, 0.2], [0.05, 0.15, 0.15, 0.2], [0.2, 0.2, 0.2, 0.2], [0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.2, 0.5], [0.3, 0.3, 0.3, 0.3], [0., 0., 0., 1.], [0.2, 0.3, 0.4, 0.5], [0.1, 0.15, 0.2, 0.25], [0.4, 0.4, 0.4, 0.4], [1., 1., 1., 1.]]
    baselines = [-0.1, 0, 0.1, 0.2]
    for coverage in coverages:
        for outcome in outcomes:
            for baseline in baselines:
                run_test(coverage, outcome, baseline)

    # Check some of the expected properties
    base = run_test([0.4, 0.3, 0.2, 0.1], [0.8, 0.9, 0.4, 0.35], 0.3, [0.705, 0.63008, 0.53])
    improved = run_test([0.4, 0.31, 0.2, 0.1], [0.8, 0.9, 0.4, 0.35], 0.3, [0.7105, 0.633936, 0.531])  # Crossing the threshold increases coverage (whereas it decreased it before)
    assert base[0] < improved[0]

    # Test effect of overriding the interaction
    base = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3)  # Baseline result
    better = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, imp_interaction='P1+P2=0.95')
    assert better[1] > base[1]
    worse = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, imp_interaction='P1+P2=0.85')
    assert worse[1] < base[1]
    same = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, imp_interaction='P1+P2=0.90')
    assert same[1] == base[1]
    better = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, imp_interaction='P1+P2=0.9,P1+P2+P3=1.0')
    assert better[1] > base[1]
    better = run_test([0.25, 0.25, 0.25, 0.25], [0.8, 0.9, 0.4, 0.35], 0.3, imp_interaction='P0+P1+P2+P3=1.0')
    assert better[2] == (0.25 * 1.0 + 0.75 * 0.3)  # Check that the nested interaction matches known result

    np.seterr(**old_settings) # Reset numpy error behaviour

if __name__ == '__main__':
    test_modalities()
    print('All tests completed successfully')
