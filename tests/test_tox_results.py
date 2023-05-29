# This script performs various tests on Result objects

import numpy as np
import atomica as at
import matplotlib.pyplot as plt
import os
import sciris as sc
import pytest


testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_export():
    P = at.demo("tb", do_run=False)
    P.run_sim(parset="default", result_name="parset1", store_results=True)
    P.run_sim(parset="default", result_name="parset2", store_results=True)
    instructions = at.ProgramInstructions(start_year=2018)
    P.run_sim(parset="default", progset="default", progset_instructions=instructions, result_name="progset1", store_results=True)
    P.run_sim(parset="default", progset="default", progset_instructions=instructions, result_name="progset2", store_results=True)

    # Test export single
    at.export_results(P.results["parset1"], tmpdir / "export_parset.xlsx")
    at.export_results(P.results["progset1"], tmpdir / "export_progset.xlsx")

    # Test export multi
    at.export_results(P.results, tmpdir / "export_multi.xlsx")
    output_ordering = ("pop", "output", "result")
    cascade_ordering = ("pop", "stage", "result")
    program_ordering = ("quantity", "program", "result")
    at.export_results(P.results, tmpdir / "export_multi_reordered.xlsx", output_ordering=output_ordering, cascade_ordering=cascade_ordering, program_ordering=program_ordering)

    # Test raw exports
    P.results["parset1"].export_raw(tmpdir / "export_raw_parset.xlsx")
    P.results["progset1"].export_raw(tmpdir / "export_raw_progset.xlsx")


def test_indexing():
    P = at.demo('usdt')
    res = P.results[0]
    res.get_variable('all_screened')[0]

    res.get_variable('scr:')

    # This example retrieves
    # [Link screen:flow (parameter screen) - undx to scr,
    #  Link diag:flow (parameter diag) - scr to dx,
    #  Link loss:flow (parameter loss) - tx to dx,
    #  Link initiate:flow (parameter initiate) - dx to tx]
    #  which might be unexpected? Should we exclude compartments that are in both characteristics somehow?
    res.get_variable(':all_screened')
    res.get_variable('all_screened:all_screened')


if __name__ == "__main__":
    # test_export()
    test_indexing()