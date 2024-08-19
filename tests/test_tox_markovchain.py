import atomica as at
import numpy as np
import os
import matplotlib.pyplot as plt
import sciris as sc
import pytest


dirname = at.parent_dir()
# np.seterr(all='raise')


@pytest.mark.parametrize("demo", at.demo_projects)
def test_functional_all_framework_databook(demo):
    # Test that all demo frameworks can be run with stochastic mode turned on
    P = at.demo(demo, do_run=False)
    P.settings.multinomial = True
    P.run_sim(result_name="DTMC")


@pytest.mark.parametrize("demo", ["sir", "udt", "tb_simple"])  # This test is expensive so only run it for a few lightweight models
def test_compare_deterministic_markovchain(demo):

    seed = 0
    N = 1000

    y_cutoff = 10  # (deterministic) Compartment values below this will not be considered for the comparisons
    index_cutoff = 1500
    y_diff_cutoff = 0

    ratio_cutoff = 0.05

    def filter_points(t, det, mc, mc_mean):
        # t_fil, det_fil, mc_fil = sc.dcp(t), sc.dcp(det), sc.dcp(mc)

        indices = np.ones(t.shape)
        indices = np.logical_and(indices, det >= y_cutoff)
        indices = np.logical_and(indices, np.arange(len(indices)) <= index_cutoff)
        indices = np.logical_and(indices, np.abs(det - mc_mean) > y_diff_cutoff)

        return t[indices], det[indices], mc[:, indices], mc_mean[indices]

    def get_array_outputs(results, output, pop):
        extracted = [None] * len(results)
        for i, res in enumerate(results):
            extracted[i] = res.model.get_pop(pop).get_variable(output)[0].vals

        array = np.stack(extracted, axis=0)
        t = results[0].model.get_pop(pop).get_variable(output)[0].t
        return t, array

    def get_average_output(results, output, pop):
        t, array = get_array_outputs(results, output, pop)
        average = np.mean(array, axis=0)

        return t, average, array

    def do_hypothesis_test(det_array, mc_results):
        import scipy

        res = scipy.stats.ttest_1samp(mc_results, det_array, keepdims=True)
        return res

    def run_simple_percent_test(P, baseline_results, mc_results):
        baseline_results = sc.promotetolist(baseline_results)
        mc_results = sc.promotetolist(mc_results)

        compartment_names = [name for name in baseline_results[0].model.framework.comps.index.values]

        max_max_diff = 0

        for compartment_name in compartment_names:
            for pop in baseline_results[0].pop_names:
                try:
                    baseline_results[0].model.get_pop(pop).get_variable(compartment_name)[0].vals
                except:
                    continue  # This population doesn't have this compartment

                t, mc_mean, mc_array = get_average_output(mc_results, compartment_name, pop)
                _, det_mean, _ = get_average_output(baseline_results, compartment_name, pop)

                t, det_mean, mc_array, mc_mean = filter_points(t, det_mean, mc_array, mc_mean)

                if len(t) == 0:  # No filtered outputs so skip this output, pop combo
                    continue

                indices = det_mean != 0
                ratio = np.ones(mc_mean.shape)
                ratio[indices] = mc_mean[indices] / det_mean[indices]
                if min(ratio) < 1 - ratio_cutoff or max(ratio) > 1 + ratio_cutoff:
                    print("RATIO", compartment_name, pop, min(ratio), max(ratio), list(zip(ratio, det_mean, mc_mean)))
                    indices = np.logical_or(ratio < 1 - ratio_cutoff, ration > 1 + ratio_cutoff)

                    raise Exception(f"The Markov Chain runs (N={len(mc_results)} differed too much from the baseline runs (N={len(baseline_results)} at starting at timestep={indices[0]}, t={t[indices[0]]}, with compartment={compartment_name}, population={pop}. Baseline={det_mean[indices[0]]}, MC={mc_mean[indices[0]]}, difference={100*(mc_mean[indices[0]]/det_mean[indices[0]] - 1):.2f}")

                max_diff = np.max(np.abs(ratio - 1))
                max_max_diff = max(max_diff, max_max_diff)

        print(f"Success: max difference {max_max_diff*100:.2f}%")

    seed = np.random.default_rng(seed).integers(2**32 - 1)

    P = at.demo(demo, do_run=False)
    res = P.run_sim(result_name="Original")

    baseline_results = [res]

    P.settings.multinomial = True
    mc_results = [None] * N
    with at.Quiet():  # Using at.Quiet should automatically reset the logging level if an exception occurs
        for i in range(N):
            this_seed = (i + seed + hash(demo)) % (2**32)
            mc_results[i] = P.run_sim(result_name=f"DTMC {i}", rng=this_seed)

    run_simple_percent_test(P, baseline_results=baseline_results, mc_results=mc_results)


if __name__ == "__main__":
    for demo in at.demo_projects:
        test_functional_all_framework_databook()
    test_compare_deterministic_markovchain("sir")
