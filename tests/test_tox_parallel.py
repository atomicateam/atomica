import atomica as at
import logging
import pytest


@pytest.mark.parametrize("do_log", [True, False])
@pytest.mark.parametrize("parallel", [True, False])
@pytest.mark.parametrize("n_samples", [1, 10])
def test_parallel(do_log, parallel, n_samples):
    """

    :param do_log: Show progress bar depending on initial logger level
    :param parallel: Use parallelization or not
    :param n_samples: Test with 1 sample or not

    :return:
    """
    P = at.demo('sir', do_run=False)

    original_level = at.logger.getEffectiveLevel()

    if not do_log:
        at.logger.setLevel(logging.WARNING)

    results = P.run_sampled_sims('default',n_samples=n_samples, parallel=parallel, num_workers = 2)
    assert len(results) == n_samples
    at.logger.setLevel(original_level)


