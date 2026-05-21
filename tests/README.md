## Automated testing

The tests in this directory with file names starting with `test_tox_*`  will automatically be run by tox/pytest.

We cannot assume that these files are being run directly from the repository, if Atomica has been installed
via pip. If only installed via pip, then Atomica won't exist in this repo folder and `atomica_path` will refer
to the `site-packages` directory instead of the repo. Therefore, inside the test, we must use 

- `au.LIBRARY_PATH` to locate the library `xlsx` files
- `at.parent_dir()` inside the test script, to locate the test dir

In practice, it can be useful to simply define the following two variables at the start of a test script:

```python
testdir = at.parent_dir()
tmpdir = testdir / "temp"
```

## Performance benchmarks

The opt-in performance suite lives in `tests/pytest_performance.py`.

Use it like this:

```bash
uv run pytest -n 0 tests/pytest_performance.py --run-perf
```

Useful options:

- `--perf-samples N` to control how many timed samples are collected per benchmark
- `--perf-warmups N` to control warmup iterations before each timed sample
- `--perf-output path.json` to write the collected measurements and model-dimension metadata to JSON

The benchmarks are intentionally skipped unless `--run-perf` is provided, and they should be run with `-n 0` so xdist does not distort timings.

Coverage currently includes:

- Representative real-model runs across small, medium, and heavy demos
- Scenario execution and sampled multi-run paths
- Save/load performance for projects with stored results
- Synthetic generated sweeps for population count and junction-heavy frameworks
