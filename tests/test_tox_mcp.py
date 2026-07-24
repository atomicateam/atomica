# Tests for the databook data-value tools exposed by the Atomica MCP server
#
# These exercise the read tools (get_populations, get_data_values, evaluate_data_values) and the
# write tools (set_data_values, clear_data_values) against the library TB databook, writing any
# modified databooks into the tests temp directory.

import atomica as at
from atomica.mcp import server as mcp_server

testdir = at.parent_dir()
tmpdir = testdir / "temp"

# The MCP tools take file paths (as an LLM would supply them), so pass strings
FW = str(at.LIBRARY_PATH / "tb_framework.xlsx")
DB = str(at.LIBRARY_PATH / "tb_databook.xlsx")


def test_mcp_get_populations():
    pops = mcp_server.get_populations(FW, DB)
    assert isinstance(pops, dict) and pops
    assert all("label" in v and "type" in v for v in pops.values())


def test_mcp_get_data_values():
    gv = mcp_server.get_data_values(FW, DB, "alive")
    assert gv["key_type"] == "population"
    assert gv["code_name"] == "alive"
    assert gv["rows"] and gv["container_tvec"]

    # A dense parameter row maps year (string key) -> value (float)
    row = gv["rows"]["0-4"]
    assert row["data"]
    assert all(isinstance(y, str) for y in row["data"])
    assert all(isinstance(v, float) for v in row["data"].values())

    # Looking up by display name resolves to the same variable
    assert mcp_server.get_data_values(FW, DB, "Population size")["code_name"] == "alive"

    # The populations filter restricts the rows returned
    filtered = mcp_server.get_data_values(FW, DB, "alive", populations=["0-4"])
    assert set(filtered["rows"]) == {"0-4"}


def test_mcp_get_data_values_connection():
    gt = mcp_server.get_data_values(FW, DB, "age")  # a transfer
    assert gt["key_type"] == "connection"
    key = next(iter(gt["rows"]))
    assert "->" in key
    row = gt["rows"][key]
    assert row["from"] == key.split("->")[0]
    assert row["to"] == key.split("->")[1]


def test_mcp_set_merge_and_clear():
    # The canonical workflow: "use a value of 12345 from 2010 onwards" for the 0-4 population
    out = str(tmpdir / "mcp_tb_onwards.xlsx")
    cleared = mcp_server.clear_data_values(FW, DB, out, "alive", populations=["0-4"], start_year=2010)
    removed = cleared["changes"][0]["removed_years"]
    assert removed and min(removed) >= 2010

    mcp_server.set_data_values(FW, out, out, "alive", rows={"0-4": {"data": {"2010": 12345}}}, mode="merge")

    reloaded = mcp_server.get_data_values(FW, out, "alive", populations=["0-4"])
    data = reloaded["rows"]["0-4"]["data"]
    assert data["2010"] == 12345.0
    assert all(float(y) <= 2010 for y in data)  # nothing after 2010 remains
    assert any(float(y) < 2010 for y in data)   # earlier history preserved

    # Flat extrapolation carries the anchored value forward
    ev = mcp_server.evaluate_data_values(FW, out, "alive", years=[2010, 2015, 2020], populations=["0-4"])
    assert ev["0-4"]["values"] == [12345.0, 12345.0, 12345.0]

    # The source databook is left untouched (writes went to `out`)
    assert "2015" in mcp_server.get_data_values(FW, DB, "alive", populations=["0-4"])["rows"]["0-4"]["data"]


def test_mcp_set_replace_and_evaluate():
    out = str(tmpdir / "mcp_tb_replace.xlsx")
    # replace: the row becomes exactly the supplied series
    mcp_server.set_data_values(FW, DB, out, "alive", rows={"0-4": {"data": {"2000": 10, "2010": 20}}}, mode="replace")
    gv = mcp_server.get_data_values(FW, out, "alive", populations=["0-4"])
    assert set(gv["rows"]["0-4"]["data"]) == {"2000", "2010"}

    # Interpolation (linear) with flat extrapolation at the ends
    ev = mcp_server.evaluate_data_values(FW, out, "alive", years=[1990, 2005, 2020], populations=["0-4"])
    assert ev["0-4"]["values"] == [10.0, 15.0, 20.0]


def test_mcp_set_assumption_and_connection():
    out = str(tmpdir / "mcp_tb_assumption.xlsx")
    # Setting an assumption alongside time data is reported as a warning
    res = mcp_server.set_data_values(FW, DB, out, "alive", rows={"0-4": {"assumption": 5.0, "data": {"2005": 9.0}}}, mode="replace")
    assert res["warnings"]

    # A pure constant can be set on a transfer connection via its 'from->to' key
    conn = next(iter(mcp_server.get_data_values(FW, DB, "age")["rows"]))
    mcp_server.set_data_values(FW, DB, out, "age", rows={conn: {"assumption": 0.33}}, mode="merge")
    assert mcp_server.get_data_values(FW, out, "age", populations=[conn])["rows"][conn]["assumption"] == 0.33


def test_mcp_clear_assumption():
    out = str(tmpdir / "mcp_tb_clear_assumption.xlsx")
    # Replace the row with a pure constant, then clear it
    mcp_server.set_data_values(FW, DB, out, "alive", rows={"0-4": {"assumption": 7.0}}, mode="replace")
    gv = mcp_server.get_data_values(FW, out, "alive", populations=["0-4"])
    assert gv["rows"]["0-4"]["assumption"] == 7.0 and gv["rows"]["0-4"]["data"] == {}

    mcp_server.clear_data_values(FW, out, out, "alive", populations=["0-4"], clear_assumption=True)
    assert mcp_server.get_data_values(FW, out, "alive", populations=["0-4"])["rows"]["0-4"]["assumption"] is None


def test_mcp_errors():
    out = str(tmpdir / "mcp_tb_errors.xlsx")

    # Unknown variable / transfer / interaction
    try:
        mcp_server.get_data_values(FW, DB, "not_a_variable")
        assert False, "expected KeyError for unknown variable"
    except KeyError:
        pass

    # Unknown row key is rejected rather than silently creating a population
    try:
        mcp_server.set_data_values(FW, DB, out, "alive", rows={"not_a_pop": {"data": {"2010": 1}}})
        assert False, "expected KeyError for unknown row"
    except KeyError:
        pass

    # Invalid mode
    try:
        mcp_server.set_data_values(FW, DB, out, "alive", rows={"0-4": {"data": {"2010": 1}}}, mode="bogus")
        assert False, "expected ValueError for bad mode"
    except ValueError:
        pass


if __name__ == "__main__":
    test_mcp_get_populations()
    test_mcp_get_data_values()
    test_mcp_get_data_values_connection()
    test_mcp_set_merge_and_clear()
    test_mcp_set_replace_and_evaluate()
    test_mcp_set_assumption_and_connection()
    test_mcp_clear_assumption()
    test_mcp_errors()
    print("All MCP databook tool tests passed")
