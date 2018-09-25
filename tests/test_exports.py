# This test validates exporting Excel files from Result objects

import atomica.ui as au
import numpy as np
import sciris as sc

P = au.Project(framework="./frameworks/framework_tb.xlsx",databook_path="./databooks/databook_tb.xlsx",do_run=False)
P.load_progbook("./databooks/progbook_tb.xlsx")
instructions = au.ProgramInstructions(start_year=2018)
result_parset = P.run_sim(parset='default',result_name='parset')
result_progset = P.run_sim(parset='default',progset='default',progset_instructions=instructions,result_name='progset')

result_parset.export('temp/result_with_progset.xlsx')
result_progset.export('temp/result_with_progset.xlsx')

result_parset.export_raw('temp/result_with_progset_raw.xlsx')
result_progset.export_raw('temp/result_with_progset.xlsx')

au.export_results([result_parset,result_progset],'temp/combined_results.zip')