import atomica.ui as au

which = ['tb','tb_simple'][0]
if which == 'tb':
    par_name = 'v_rate'
    pop_name = '0-4'
elif which == 'tb_simple':
    par_name = 'vac_rate'
    pop_name = 'adults'

P = au.demo(which=which, do_run=False)

# Test single year reconciliation
program_start_year = 2018.
original_progset = P.progsets[0]
parset = P.parsets[0]
reconciled_progset, progset_comparison, parameter_comparison = au.reconcile(project=P,parset=P.parsets[0],progset=original_progset,reconciliation_year=program_start_year,unit_cost_bounds=0.2)

instructions = au.ProgramInstructions(start_year=program_start_year)
parset_result = P.run_sim(parset=P.parsets[0],result_name='Parset')
original_result = P.run_sim(parset=P.parsets[0],progset=original_progset,progset_instructions=instructions,result_name='Original')
reconciled_result = P.run_sim(parset=P.parsets[0],progset=reconciled_progset,progset_instructions=instructions,result_name='Reconciled')

print(progset_comparison)
print(parameter_comparison)

for par,pop in [(par_name,pop_name)]:
    d = au.PlotData([parset_result, original_result, reconciled_result],outputs=par,pops=pop,project=P)
    au.plot_series(d,axis='results')

reconciled_progset.save('temp/reconciled_progset.xlsx')

# Test multi year reconciliation

program_start_year = 2018.
eval_range = [2018.,2020.]
original_progset = P.progsets[0]
parset = P.parsets[0]
reconciled_progset, progset_comparison, parameter_comparison = au.reconcile(project=P,parset=P.parsets[0],progset=original_progset,reconciliation_year=program_start_year,unit_cost_bounds=0.2, eval_range=eval_range)

instructions = au.ProgramInstructions(start_year=program_start_year)
parset_result = P.run_sim(parset=P.parsets[0],result_name='Parset')
original_result = P.run_sim(parset=P.parsets[0],progset=original_progset,progset_instructions=instructions,result_name='Original')
reconciled_result = P.run_sim(parset=P.parsets[0],progset=reconciled_progset,progset_instructions=instructions,result_name='Reconciled')

print(progset_comparison)
print(parameter_comparison)

for par,pop in [(par_name,pop_name)]:
    d = au.PlotData([parset_result, original_result, reconciled_result],outputs=par,pops=pop,project=P)
    au.plot_series(d,axis='results')
