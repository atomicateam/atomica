# import unittest
import atomica as at
import os
import pytest
import numpy as np
import sciris as sc
import at_tools as att

# class MyTestCase(unittest.TestCase):
#     def test_something(self):
#         self.assertEqual(True, False)  # add assertion here
#
#
# if __name__ == '__main__':
#     unittest.main()


# Basic minimum working product test to verify all yaml features run

testdir = at.parent_dir()
tmpdir = testdir / 'temp'
yaml_dir = 'yaml_tests'

# List yaml files in directory
yaml_files = list()
for f in os.listdir(testdir/yaml_dir):
    yaml_files.append(f)


def run_auto_calibration(proj):
    """Run an automatic calibration

    :param proj: A Project object
    :return:
    """

    proj.calibrate(max_time=10, new_name="auto")

    return


# Testing optimizations and calibrations could be expensive
# Using the parametrize decorator means Pytest will treat
# each function call as a separate test, which can be run in parallel
# simply by adding `pytest -n 4` for instance. Or via tox
# `tox -- -o -n 4` (because the default config is to use n=2 for TravisCI)
@pytest.mark.parametrize("yaml_fname", yaml_files)
def test_yaml_calibration(yaml_fname):

    #set these once outside test itself?
    fw_ver = '2_8_1'
    db_ver = '2_8'
    country = 'PAK'
    dis = 'typh'

    F = at.ProjectFramework(f"framework_bivalent_combined_v{fw_ver}.xlsx")
    D = at.ProjectData.from_spreadsheet(f"databook_bivalent_{country}_v{db_ver}.xlsx", framework=F)
    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.update_time_vector(start=2000, end=2050, dt=1/52)
    cal = P.make_parset()

    print(f"\n\nTESTING yaml config {yaml_fname}")

    #import yaml config
    config_file_path = f'{yaml_dir}/{yaml_fname}'
    config = att.ProjectConfig.from_yaml(config_file_path) #TODO change this to not rely on atomica tools?
    #or can import in all the diff ways - make function

    #run calibration with yaml instructions
    newcal = config.run_calibration(P, parset=cal, quiet=False, savedir=tmpdir, save_intermediate=False, verbose=0, max_time=1)
    #also run in several diff ways? Or have a separate test for that?

    # Test saving the calibration
    # save()

    print("Test complete")


if __name__ == "__main__":

    np.seterr(all="raise")
    for f in yaml_files:
        test_yaml_calibration(f)
