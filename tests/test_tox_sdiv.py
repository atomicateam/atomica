# Test safe division in function_parser

from atomica.function_parser import sdiv
import numpy as np


def test_sdiv():

    with np.errstate(divide='ignore'): # Suppress expected numpy division by zero warning

        # Both scalar
        assert sdiv(1, 2) == 0.5
        assert sdiv(1, 0) == np.inf
        assert sdiv(0, 1) == 0
        assert sdiv(0, 0) == 0

        # Numerator vector
        assert np.allclose(sdiv(np.array(np.array([0, 1])), 0), np.array([0, np.inf]), equal_nan=True)

        # Denominator vector
        assert np.allclose(sdiv(0, np.array([0, 1])), np.array([0, 0]), equal_nan=True)

        # Both vector
        assert np.allclose(sdiv(np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])), np.array([0, 0, np.inf, 1]), equal_nan=True)

        # Different shape
        assert np.allclose(sdiv(np.array([[0, 0], [1, 1]]), np.array([[0, 1], [0, 1]])), np.array([[0, 0], [np.inf, 1]]), equal_nan=True)


if __name__ == "__main__":
    test_sdiv()
