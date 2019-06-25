import atomica as at
P = at.demo(which='tb')

instructions = at.ProgramInstructions(start_year=2018)
result1 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Default budget')
#
# # Override the default budget (these are relatively minor tweaks)
alloc = {'BCG': 350000.0,
 'PCF': 26568000.0,
 'ACF': 24282133.33333333,
 'ACF-p': 803333.3333333334,
 'HospDS': 119461100.0,
 'HospMDR': 8305000.0,
 'HospXDR': 1446000.0,
 'AmbDS': 0.0,
 'AmbMDR': 0.0,
 'XDRnew': 761200.0,
 'PrisDS': 1114500.0,
 'PrisDR': 200000.0}
instructions = at.ProgramInstructions(alloc=alloc,start_year=2018)
result2 = P.run_sim(P.parsets[0],P.progsets[0],progset_instructions=instructions,result_name='Modified budget')

# SPENDING PLOTS

# Stacked time series of spending
d = at.PlotData.programs(result1)
at.plot_series(d,plot_type='stacked')

# Stacked bar graph for single time
d = at.PlotData.programs(result1)
d.interpolate(2018)
at.plot_bars(d,stack_outputs='all')

# Stacked bar graph, for different times
d = at.PlotData.programs(result1)
d.interpolate([2018,2020])
at.plot_bars(d,stack_outputs='all')

# Compare budgets at a single point in time
d = at.PlotData.programs([result1,result2])
d.interpolate(2018)
at.plot_bars(d,stack_outputs='all')

# Select a subset of programs
outputs = ['HospDS','HospMDR','HospXDR']
d = at.PlotData.programs([result1,result2],outputs=outputs)
d.interpolate(2018)
at.plot_bars(d,stack_outputs='all')

# Aggregate programs
outputs = {'Hosp':['HospDS','HospMDR','HospXDR']}
d = at.PlotData.programs([result1,result2],outputs=outputs)
d.interpolate(2018)
at.plot_bars(d,stack_outputs='all')

# Aggregate spending over time
# This plot shows the total spend from 2020-2030
# so it's 10x the plot for just 2018
d = at.PlotData.programs([result1,result2],t_bins=[2020,2030])
at.plot_bars(d,stack_outputs='all')

## COVERAGE PLOTS

d = at.PlotData.programs(result1,quantity='coverage_number')
at.plot_series(d,plot_type='stacked')

d = at.PlotData.programs(result1,quantity='coverage_eligible')
at.plot_series(d,plot_type='stacked')

d = at.PlotData.programs(result1,quantity='coverage_fraction')
at.plot_series(d,plot_type='line')

d = at.PlotData.programs(result1,accumulate='integrate')
at.plot_series(d,plot_type='stacked')
