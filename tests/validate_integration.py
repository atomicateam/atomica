# This is a special test to check that the integration is the same from version to version
# The intended usage is to verify that changes to the code do not affect integration outputs
# The key check is that the compartment sizes and flow rates come out the same as before
#
# The workflow for this function is that the first time it is run, it will write some saved
# result files. The second time it is run, it will re-run the simulations and compare them
# to the saved files. The saved files are not included with Git. When making changes,
# developers should first delete and regenerate the cache files. Then, re-run this script
# before committing the updates to the repository.
#
# The motivation for this workflow is that changes to the integration are expected to happen
# from time to time, and this way the repository size won't irreversibly grow due
# to old results being contained in the repo


import atomica as at
import os
import pytest
import numpy as np

# List available models based on which framework files exist
models = list()
for f in os.listdir(at.LIBRARY_PATH):
    if f.endswith("_framework.xlsx") and not f.startswith("~$"):
        models.append(f.replace("_framework.xlsx", ""))


def validate(r1, r2):
    for p1, p2 in zip(r1.model.pops, r2.model.pops):
        for v1 in p1.comps + p1.characs + p1.pars + p1.links:  # For every variable in the old one
            if isinstance(v1, at.model.Link):
                try:
                    v2 = p2.get_variable("%s:%s:%s" % (v1.source.name, v1.dest.name, v1.parameter.name))[0]
                    assert np.allclose(v1.vals, v2.vals, equal_nan=True)  # Default tolerances are rtol=1e-05, atol=1e-08
                except at.system.NotFoundError:
                    print('Could not find "%s" in saved output, continuing' % (v1.name))
            else:
                try:
                    v2 = p2.get_variable(v1.name)[0]
                    assert np.allclose(v1.vals, v2.vals, equal_nan=True)  # Default tolerances are rtol=1e-05, atol=1e-08
                except at.system.NotFoundError:
                    print('Could not find "%s" in saved output, continuing' % (v1.name))

    print("Validation passed")


@pytest.mark.parametrize("model", models)
def test_validate_model(model):

    testdir = at.parent_dir()
    tmpdir = testdir / "temp"

    framework_file = at.LIBRARY_PATH / f"{model}_framework.xlsx"
    databook_file = at.LIBRARY_PATH / f"{model}_databook.xlsx"
    progbook_file = at.LIBRARY_PATH / f"{model}_progbook.xlsx"

    # Only check if both parset and progset are present
    # Not meant to be exhaustive, just reasonably comprehensive
    if not os.path.isfile(databook_file) or not os.path.isfile(progbook_file):
        return

    P1 = at.Project(framework=framework_file, databook=databook_file, do_run=False)
    P1.load_progbook(progbook_file)
    P1.update_settings(sim_end=2025)  # Make sure we run until 2025

    P1.run_sim(P1.parsets[0], result_name="parset", store_results=True)
    P1.run_sim(P1.parsets[0], P1.progsets[0], at.ProgramInstructions(start_year=2018), result_name="progset", store_results=True)

    fname = tmpdir / ("validation_" + model + ".prj")
    if os.path.isfile(fname):
        P2 = at.Project.load(fname)
        print("Validating %s parset" % (model))
        validate(P1.results["parset"], P2.results["parset"])
        validate(P1.results["progset"], P2.results["progset"])
    else:
        print("Regenerating  %s parset" % (model))
        P1.save(fname)
        raise Exception('Regenerated results - re-run to perform comparison')


if __name__ == "__main__":
    np.seterr(all="raise", under="ignore")
    for m in models:
        test_validate_model(m)
