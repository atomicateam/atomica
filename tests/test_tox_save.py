import numpy as np
import atomica as at

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"


def test_save():

    P = at.demo("sir")
    P.save(tmpdir / "test_project_save.prj")
    P2 = at.Project.load(tmpdir / "test_project_save.prj")
    P2.run_sim()


if __name__ == "__main__":
    test_save()
