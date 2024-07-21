import pytest
import matplotlib.pyplot as plt


@pytest.fixture(scope="function", autouse=True)
def close_figures():
    yield
    plt.close("all")


# conftest.py
def pytest_collection_modifyitems(items):
    for i, item in enumerate(items):
        if item.name == "test_model[tb]":
            items.pop(i)
            items.insert(0, item)
            break
