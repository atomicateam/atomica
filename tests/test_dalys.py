# This script demonstrates plotting DALYs and DALY-related quantities for the
# reference implementation in the TB model

import atomica as at
import numpy as np

P = at.demo('tb')

d = at.PlotData(P.results[0],outputs='daly_rate',pops='total',accumulate='integrate',project=P)
figs=at.plot_series(d,axis='pops')

d = at.PlotData(P.results[0],outputs=['yll_rate','yld_rate','daly_rate'],pops='total',t_bins='all')
d.outputs['yll_rate'] = 'Years lost to deaths'
d.outputs['yld_rate'] = 'Years lost to disease'
d.outputs['daly_rate'] = 'DALYs'
figs=at.plot_bars(d,stack_outputs=[['yll_rate','yld_rate']])

d = at.PlotData(P.results[0],outputs=['yld_rate','ac_inf'],pops='total',accumulate='integrate',project=P)
figs=at.plot_series(d,axis='outputs')

