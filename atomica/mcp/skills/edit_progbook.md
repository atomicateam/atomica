# Edit a Progbook

Reliably modify an Atomica program book (program spending, unit costs, coverage/capacity, and outcome functions) by loading it as a `ProgramSet`, editing the program time series and outcomes through the API, then saving. Use when the user asks to change, add, remove, or bulk-edit programs or their costs/coverage/outcomes in a progbook `.xlsx`.

## Why not edit the spreadsheet directly

As with databooks, do **not** edit progbook cells by coordinate. A `ProgramSet` regenerates the full workbook layout on save, so editing through the object model keeps program tables, targeting, and cost/coverage/outcome blocks consistent.

## Steps

1. **Load** the progbook against its framework and the project data (a progbook is defined relative to a framework's programs and the databook's populations):
   ```python
   import atomica as at
   F = at.ProjectFramework("framework.xlsx")
   D = at.ProjectData.from_spreadsheet("databook.xlsx", framework=F)
   PS = at.ProgramSet.from_spreadsheet("progbook.xlsx", framework=F, data=D)
   # If you already have a Project P, `project=P` can supply framework+data.
   ```

2. **Locate a program.** `PS.programs` is an odict keyed by program code name (`PS.programs["BCG"]`). Each `Program` holds its targeting plus `TimeSeries` for spending, unit cost, capacity/coverage, and saturation.

3. **Edit program time series** the same way as databook data — by year, via `insert` / `remove` / `assumption` (the exact attribute names are on the `Program` object; inspect `vars(PS.programs[name])` if unsure):
   ```python
   prog = PS.programs["BCG"]
   prog.spend_data.insert(2022, 1.0e6)     # annual spend
   prog.unit_cost.insert(2022, 12.5)       # cost per coverage unit
   prog.capacity.insert(2022, 500000)      # capacity/coverage (if used)
   ```

4. **Edit outcomes** (how program coverage maps to parameter values): outcome functions live in `PS.covouts`, keyed by (parameter, population). Adjust the baseline and the per-program outcome values there.

5. **Add or remove structure:** `PS.add_program(code, full_name)`, `PS.remove_program(name)`, and `PS.add_comp(...)` / `PS.add_par(...)` to make a compartment or parameter targetable by programs.

6. **Save:**
   ```python
   PS.save("progbook_v2.xlsx")
   ```
   Re-load the saved file and run a program scenario to confirm coverage and outcomes behave as intended.
