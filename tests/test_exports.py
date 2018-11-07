# This test validates exporting Excel files from Result objects

import atomica as at
import numpy as np
import sciris as sc

tmpdir = at.atomica_path(['tests','temp'])
P = at.demo('tb')
instructions = at.ProgramInstructions(start_year=2018)
result_parset = P.run_sim(parset='default',result_name='parset')
result_progset = P.run_sim(parset='default',progset='default',progset_instructions=instructions,result_name='progset')

result_parset.export(tmpdir + 'result_with_progset.xlsx')
result_progset.export(tmpdir + 'result_with_progset.xlsx')

result_parset.export_raw(tmpdir + 'result_with_progset_raw.xlsx')
result_progset.export_raw(tmpdir + 'result_with_progset.xlsx')

at.export_results([result_parset,result_progset],tmpdir + 'combined_results.zip')