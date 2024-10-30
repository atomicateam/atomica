# Test quiet context

import atomica as at

testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_file_logging():
    fname = tmpdir / "log.txt"

    at.start_logging(fname)
    at.logger.info("test")

    # Check that after logging is stopped, output is not added to the file
    at.stop_logging()
    at.logger.info("test2")
    assert open(fname).readlines()[-1].strip().split()[-1] == "test"

    at.start_logging(fname)
    at.logger.info("test3")
    at.start_logging(fname)
    at.logger.info("test4")
    at.start_logging(fname, reset=True)
    at.logger.info("test5")


def test_quiet():
    # Nothing should be printed out by this test
    logger_level = at.logger.getEffectiveLevel()

    with at.Quiet():
        at.demo("sir")

    with at.Quiet(False):
        at.demo("sir")

    assert at.logger.getEffectiveLevel() == logger_level, "Logger level has been permanently changed"


if __name__ == "__main__":
    test_quiet()
    test_file_logging()
