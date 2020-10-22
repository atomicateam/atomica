# Test quiet context

import atomica as at


def test_quiet():
    # Nothing should be printed out by this test
    logger_level = at.logger.getEffectiveLevel()

    with at.Quiet():
        at.demo('sir')

    with at.Quiet(False):
        at.demo('sir')

    assert at.logger.getEffectiveLevel() == logger_level, "Logger level has been permanently changed"


if __name__ == '__main__':
    test_quiet()
