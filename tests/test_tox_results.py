## This script performs various tests on Result objects

import numpy as np
import atomica as at
import matplotlib.pyplot as plt
import os
import sciris as sc
import pytest


tmpdir = at.atomica_path(['tests','temp'])

def test_export():
    P = at.demo('tb',do_run=False)
    P.run_sim(parset='default',result_name='parset1')
    P.run_sim(parset='default',result_name='parset2')
    instructions = at.ProgramInstructions(start_year=2018)
    P.run_sim(parset='default',progset='default',progset_instructions=instructions,result_name='progset1')
    P.run_sim(parset='default',progset='default',progset_instructions=instructions,result_name='progset2')

    # Test export single
    at.export_results(P.results['parset1'],tmpdir + 'export_parset.xlsx')
    at.export_results(P.results['progset1'],tmpdir + 'export_progset.xlsx')

    # Test export multi
    at.export_results(P.results,tmpdir + 'export_multi.xlsx')
    output_ordering = ('pop', 'output', 'result')
    cascade_ordering = ('pop','stage','result')
    program_ordering = ('quantity', 'program', 'result')
    at.export_results(P.results,tmpdir + 'export_multi_reordered.xlsx',output_ordering=output_ordering,cascade_ordering=cascade_ordering,program_ordering=program_ordering)

    # Test raw exports
    P.results['parset1'].export_raw(tmpdir + 'export_raw_parset.xlsx')
    P.results['progset1'].export_raw(tmpdir + 'export_raw_progset.xlsx')

if __name__ == '__main__':
    test_export()
