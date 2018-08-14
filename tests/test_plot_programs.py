import atomica.ui as au
P = au.demo(which='tb')

instructions = au.ProgramInstructions()
result1 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Default budget')

d = au.PlotData.programs(result1,quantity='coverage')
au.plot_series(d,plot_type='stacked')

# Override the default budget (these are relatively minor tweaks)
alloc = dict()
alloc['BCG'] = 28792743
alloc['MS-PHC'] = 91011837
alloc['ENH-MS-PHC'] = 0
alloc['MS-HR'] = 0
alloc['CT-DS'] = 8066623
alloc['CT-DR'] = 1050575
alloc['ACF-PLHIV'] = 198656962
alloc['DS-TB'] = 81512361
alloc['Old MDR'] = 2191976
alloc['Old MDR/BDQ'] = 2742988
alloc['MDR/BDQ'] = 0
alloc['KM-SC'] = 0
alloc['BDQ-SC'] = 0
alloc['XDR-Current'] = 412308
alloc['XDR-new'] = 0
alloc['PLHIV/DS-TB'] = 40533507
alloc['PLHIV/Old MDR'] = 9888870
alloc['PLHIV/Old MDR-BDQ'] = 9712783
alloc['PLHIV/New MDR'] = 0
alloc['PLHIV/Old XDR'] = 4488215
alloc['PLHIV/New XDR'] = 0
alloc['Pris DS-TB'] = 0
alloc['Pris MDR'] = 0
alloc['Pris XDR'] = 0
alloc['Min DS-TB'] = 0
alloc['Min MDR'] = 0
alloc['Min XDR'] = 0
alloc['PCF-HIV-'] = 8020991
alloc['PCF-HIV+'] = 6956362
instructions = au.ProgramInstructions(alloc=alloc,start_year=2018)
result2 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Modified budget')

# Stacked time series of spending
d = au.PlotData.programs(result1)
au.plot_series(d,plot_type='stacked')

# Stacked bar graph for single time
d = au.PlotData.programs(result1)
d.interpolate(2018)
au.plot_bars(d,stack_outputs='all')

# Stacked bar graph, for different times
d = au.PlotData.programs(result1)
d.interpolate([2018,2020])
au.plot_bars(d,stack_outputs='all')

# Compare budgets at a single point in time
d = au.PlotData.programs([result1,result2])
d.interpolate(2018)
au.plot_bars(d,stack_outputs='all')

# Select a subset of programs
outputs = ['PLHIV/DS-TB','PLHIV/Old MDR','PLHIV/Old MDR-BDQ','PLHIV/New MDR','PLHIV/Old XDR','PLHIV/New XDR']
d = au.PlotData.programs([result1,result2],outputs=outputs)
d.interpolate(2018)
au.plot_bars(d,stack_outputs='all')

# Aggregate programs
outputs = {'PLHIV':['PLHIV/DS-TB','PLHIV/Old MDR','PLHIV/Old MDR-BDQ','PLHIV/New MDR','PLHIV/Old XDR','PLHIV/New XDR']}
d = au.PlotData.programs([result1,result2],outputs=outputs)
d.interpolate(2018)
au.plot_bars(d,stack_outputs='all')

# Aggregate spending over time
# This plot shows the total spend from 2020-2030
# so it's 10x the plot for just 2018
d = au.PlotData.programs([result1,result2],t_bins=[2020,2030])
au.plot_bars(d,stack_outputs='all')

