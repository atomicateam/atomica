import atomica.ui as au
P = au.demo(which='diabetes',do_run=False)

program_start_year = 2016.
original_progset = P.progsets[0]
parset = P.parsets[0]
reconciled_progset, progset_comparison, parameter_comparison = au.reconcile(project=P,parset=P.parsets[0],progset=original_progset,reconciliation_year=program_start_year,unit_cost_bounds=0.2)

instructions = au.ProgramInstructions(start_year=program_start_year)
parset_result = P.run_sim(parset=P.parsets[0],result_name='Parset')
original_result = P.run_sim(parset=P.parsets[0],progset=original_progset,progset_instructions=instructions,result_name='Original')
reconciled_result = P.run_sim(parset=P.parsets[0],progset=reconciled_progset,progset_instructions=instructions,result_name='Reconciled')

print(progset_comparison)
print(parameter_comparison)

#for par,pop in [('v_rate','0-4')]:
#    d = au.PlotData([parset_result, original_result, reconciled_result],outputs=par,pops=pop,project=P)
#    au.plot_series(d,axis='results')
#
reconciled_progset.save('temp/reconciled_progset.xlsx')