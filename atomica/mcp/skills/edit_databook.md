# Edit a Databook

Reliably modify the data in an Atomica databook (population sizes, calibration targets, program-independent parameter values, transfers) by loading it as a `ProjectData` object and editing time series addressed by (variable, population, year), then saving. Use when the user asks to change, add, fix, port, disaggregate, or bulk-edit values in a databook `.xlsx`.

## Why not edit the spreadsheet directly

Do **not** edit databook cells by coordinate (openpyxl/win32com row+column writes). Databook sheets pack many tables onto one sheet; inserting or shifting any row (e.g. adding a "Total" row) moves every table below it, so coordinate-based writes silently land in the wrong table. The `ProjectData` API addresses data by (variable, population, year) and regenerates the entire sheet layout on save, so placement cannot drift.

## Steps

1. **Load** the databook against its framework:
   ```python
   import atomica as at
   F = at.ProjectFramework("framework.xlsx")
   D = at.ProjectData.from_spreadsheet("databook.xlsx", framework=F)
   ```

2. **Find the variable code name.** If the user names a concept ("incidence", "births"), use the `list_variables(framework_path, search_terms=[...])` tool to get the code name. Databook quantities are compartments/characteristics/parameters whose code names key `D.tdve`.

3. **Edit a time series.** `D.get_ts(name, key)` returns the `TimeSeries` for one (variable, population); for a comp/charac/par, `key` is the population code:
   ```python
   ts = D.get_ts("inci_per_100k", "0-4")   # or D.tdve["inci_per_100k"].ts["0-4"]
   ts.insert(2015, 361.0)   # set/overwrite the value at a year (creates the point if absent)
   ts.get(2015)             # read a value
   ts.remove(2001)          # delete a year's point
   ts.assumption = 0.33     # set a constant (time-independent) value instead of yearly points
   ts.units = "fraction"    # metadata; ts.sigma = uncertainty
   ```
   For a **transfer or interaction**, `name` is the transfer code and `key` is a `(from_pop, to_pop)` tuple: `D.get_ts("aging", ("0-4","5-11"))`.

4. **Add rows/structure** when needed (no manual row insertion):
   - Extra aggregate row (e.g. a national "Total"): assign a new key in the TDVE's `ts` dict —
     `D.tdve["inci_per_100k"].ts["tot"] = at.TimeSeries(units="fraction")`, then `insert(...)`. Non-population keys like a Total row are allowed and are not validated against the population list.
   - Population / transfer / interaction: `D.add_pop(code, full_name, pop_type)`, `D.add_transfer(...)`, `D.add_interaction(...)`, plus `rename_pop` / `remove_pop` / `remove_transfer`.
   - Change the year columns of every table: `D.change_tvec(np.arange(2000, 2041))`.

5. **Disaggregating one population into several** (e.g. an age band into sub-bands): weight **counts** (cases, notifications, births, population) by the sub-populations' **population size** — never split equally. Replicate **rates and proportions** (per-100k, prevalence, treatment-outcome fractions) unchanged to each sub-population. National totals belong in a single aggregate ("Total") row, not split.

6. **Validate and save:**
   ```python
   D.validate(F)              # raises on structural/data problems; fix before saving
   D.save("databook_v2.xlsx")
   ```
   If `validate` raises `AttributeError: 'TimeDependentConnections' object has no attribute 'full'`, that is masking a real "population not recognized" error in a transfer/interaction (a pop name that is not in `D.pops`); check the transfer's from/to population codes.
