import pytest
import matplotlib.pyplot as plt
import json
import os
import platform
import sys
from pathlib import Path


@pytest.fixture(scope="function", autouse=True)
def close_figures():
    yield
    plt.close("all")


def pytest_addoption(parser):
    group = parser.getgroup("atomica-perf")
    group.addoption("--run-perf", action="store_true", default=False, help="Run Atomica performance benchmarks")
    group.addoption("--perf-output", action="store", default=None, help="Optional path to write Atomica performance benchmark results as JSON")
    group.addoption("--perf-samples", action="store", type=int, default=3, help="Number of timed samples to collect for each performance benchmark")
    group.addoption("--perf-warmups", action="store", type=int, default=1, help="Number of warmup iterations to run before each timed performance benchmark sample")


def pytest_configure(config):
    config.addinivalue_line("markers", "perf: opt-in performance benchmark")
    config._atomica_perf_results = []


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-perf"):
        return

    skip_perf = pytest.mark.skip(reason="performance tests are opt-in; pass --run-perf to enable them")
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip_perf)


def pytest_runtest_setup(item):
    if "perf" in item.keywords and os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.skip("performance benchmarks should be run serially; re-run with -n 0")


def pytest_sessionfinish(session, exitstatus):
    output_path = session.config.getoption("--perf-output")
    if not output_path:
        return

    payload = {
        "platform": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "results": session.config._atomica_perf_results,
    }
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
