import atomica.ui as au
P = au.demo(which='tb',do_run=False)

original_progset = P.progsets[0]
parset = P.parsets[0]
reconciled_parset = au.reconcile(project=P,parset=P.parsets[0],progset=original_progset,reconciliation_year=2018,unit_cost_bounds=0.2)
