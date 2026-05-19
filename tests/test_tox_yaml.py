# import unittest
import atomica as at
import os
import pytest
import numpy as np
import sciris as sc

# Basic minimum working product test to verify all yaml features run
testdir = at.parent_dir()
tmpdir = testdir / "temp"
yaml_dir = testdir / "yaml_tests"

# List yaml files in directory
yaml_files = list(yaml_dir.glob("*.yaml"))


@pytest.fixture()
def project():
    P = at.demo("udt_dyn", do_run=False)
    P.settings.update_time_vector(start=2000, end=2050, dt=1 / 52)
    return P


def test_save_intermediate(project):
    project.calibrate(yaml=yaml_files[0], parset=project.make_parset(), quiet=False, savedir=tmpdir / "yaml_save_test", save_intermediate=True, verbose=0, max_time=0.1)


@pytest.mark.parametrize("yaml_fname", yaml_files, ids=[x.stem for x in yaml_files])
def test_yaml_calibration(project, yaml_fname):

    # TODO - this demo project has only one population. It would be good
    # to have a test with multiple populations and where there is a space in the population name

    print(f"\n\nTESTING yaml config {yaml_fname}")

    # run calibration with yaml instructions
    # config_file_path = yaml_dir/yaml_fname
    # print(config_file_path)
    project.calibrate(yaml=yaml_fname, parset=project.make_parset(), quiet=False, savedir=tmpdir, save_intermediate=False, verbose=0, max_time=0.1)

    # or can import in all the diff ways - make function
    # also run in several diff ways? Or have a separate test for that?

    # Test saving the calibration
    # save()

    print("Test complete")


if __name__ == "__main__":

    np.seterr(all="raise")
    for f in yaml_files:
        test_yaml_calibration(f)
