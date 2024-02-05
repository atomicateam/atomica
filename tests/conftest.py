import pytest
import matplotlib.pyplot as plt


@pytest.fixture(scope="function", autouse=True)
def close_figures():
    yield
    plt.close("all")
