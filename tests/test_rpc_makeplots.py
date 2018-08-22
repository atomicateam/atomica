# Make demo project and default budget run
import atomica.ui as au
import sys

sys.path.append(au.atomica_path())
from atomica_apps.rpcs import get_budget_plot

P = au.demo(which='tb',do_run=False)
instructions = au.ProgramInstructions()
result1 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Default budget')

# Do a simple budget scenario so that we have different spending
alloc = {'ACF-PLHIV': 198656962,'BCG': 28792743,'BDQ-SC': 0,'CT-DR': 1050575,'CT-DS': 8066623,'DS-TB': 81512361,'ENH-MS-PHC': 0,'KM-SC': 0,'MDR/BDQ': 0,'MS-HR': 0,'MS-PHC': 91011837,'Min DS-TB': 0,'Min MDR': 0,'Min XDR': 0,'Old MDR': 2191976,'Old MDR/BDQ': 2742988,'PCF-HIV+': 6956362,'PCF-HIV-': 8020991,'PLHIV/DS-TB': 40533507,'PLHIV/New MDR': 0,'PLHIV/New XDR': 0,'PLHIV/Old MDR': 9888870,'PLHIV/Old MDR-BDQ': 9712783,'PLHIV/Old XDR': 4488215,'Pris DS-TB': 0,'Pris MDR': 0,'Pris XDR': 0,'XDR-Current': 412308,'XDR-new': 0}
instructions = au.ProgramInstructions(alloc=alloc,start_year=2018)
result2 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Modified budget')

# Do a budget scenario with time-varying spending
alloc = {'ACF-PLHIV': au.TimeSeries([2018,2030],[2e8,1.5e8]),'BCG': au.TimeSeries([2018,2025],[2e7,3e7])}
instructions = au.ProgramInstructions(alloc=alloc,start_year=2018)
result3 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Time-varying budget')

figs = get_budget_plot(result1,2018)
figs = get_budget_plot(result1,[2018,2019])
figs = get_budget_plot([result1,result2],2018)
figs = get_budget_plot([result1,result2],[2018,2019])