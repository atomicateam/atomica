import atomica as at
import sciris as sc
import os

# # P = at.Project(framework='dummy_framework.xlsx',databook='dummy_databook.xlsx')
# # # P.run_sim()
# # P = at.demo('tb',do_run=True)
# # P.results[0].plot()
# # P = at.Project.load('asdf2.prj')
#
# # P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# # P.load_databook(at.LIBRARY_PATH+'tb_databook.xlsx')
# P = at.demo('tb',do_run=True)
#
#


# Test that the timed databook can be written with purely
testdir = os.path.abspath(os.path.join(os.path.dirname(__file__),'tests')) + os.sep  # Must be relative to current file to work with tox
F = at.ProjectFramework(testdir+'timed_test_framework.xlsx')
D = at.ProjectData.new(framework=F,tvec=[2018],pops=1,transfers=0)
sc.tic()
D.save('test.xlsx')
P = at.Project(framework=F,databook='test.xlsx',do_run=False)
P.settings.sim_dt = 1/12
P.settings.sim_start = 2018
P.settings.sim_end = 2020

# Baseline sim
# res = P.run_sim('default')
# sc.toc()
# d = at.PlotData(res,[':inf','inf:','inf'])
# at.plot_series(d)

# Test a spike in infections
# ps = P.parsets[0].copy()
# ps.pars['foi'].ts[0].insert(2018,24)
# ps.pars['foi'].ts[0].insert(2019,100)
# ps.pars['foi'].ts[0].insert(2019+1/12,24)
# ps.pars['foi'].smooth(P.settings.tvec,'previous')
# res2 = P.run_sim(ps)
# d = at.PlotData(res2,[':inf','inf:','inf'])
# at.plot_series(d)

# Test junction-like behaviour where the compartment empties every timestep
ps = P.parsets[0].copy()
ps.pars['nat_rec'].ts[0].insert(None,12) # Sub-timestep size
res2 = P.run_sim(ps)
d = at.PlotData(res2,[':inf','inf:','inf'])
at.plot_series(d)


P.framework.pars.at['nat_rec','timed'] = 'n'
res3 = P.run_sim(ps)

at.logger.setLevel('WARNING')


# import networkx as nx
# import pylab as plt
# from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
# import pygraphviz as pgv
#
# G = nx.DiGraph()
# G.add_node("A",rank=0)
# G.add_nodes_from(['B','C','D'],style='filled',fillcolor='red')
# G.add_nodes_from(['D','F','G'])
# G.add_nodes_from(['H'],label='target')
# G.add_edge('A','B',arrowsize=2.0)
# G.add_edge('A','C',penwidth=2.0)
# G.add_edge('A','D')
# G.add_edges_from([('B','E'),('B','F')],color='blue')
# G.add_edges_from([('C','E'),('C','G')])
# G.add_edges_from([('D','F'),('D','G')])
# G.add_edges_from([('E','H'),('F','H'),('G','H')])
#
# # set defaults
# G.graph['graph']={'rankdir':'TD'}
# G.graph['node']={'shape':'circle'}
# G.graph['edges']={'arrowsize':'4.0'}
#
# A = to_agraph(G)
# print(A)
# A.layout('dot')
# A.draw('abcd.png')


# P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# import sciris as sc
# sc.tic()
# P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# sc.toc()

# P = sc.loadobj('Mztest local with error.prj')
#
# # P.optims[2].json['objective_weights'][':ddis'] = P.optims[2].json['objective_weights']['ddis']
# # P.optims[2].json['objective_labels'][':ddis'] = P.optims[2].json['objective_labels']['ddis']
# # del P.optims[2].json['objective_weights']['ddis']
# #
# # P.optims[2].json['objective_weights'][':acj'] = P.optims[2].json['objective_weights']['acj']
# # P.optims[2].json['objective_labels'][':acj'] = P.optims[2].json['objective_labels']['acj']
# # del P.optims[2].json['objective_weights']['acj']
# #
# # P.optims[2].json['method'] = 'pso'
# # P.optims['Default money optimization (2)'].json['objective_weights'][':ddis']=30
# results = P.run_optimization('Error Optim', maxtime=float(300), store_results=False)
#
# #
#
# instructions = at.ProgramInstructions(alloc=P.progsets[-1],start_year=2017)
# res1 = P.run_sim(parset=-1,progset=-1,progset_instructions=instructions2,result_name='Baseline')
#
# alloc = {x.name:0 for x in P.progsets[0].programs.values()}
# instructions = at.ProgramInstructions(alloc=alloc,start_year=2017)
# res2 = P.run_sim(parset=-1,progset=-1,progset_instructions=instructions,result_name='No spending')
#
# alloc = {x.name: 0.5*x.spend_data.interpolate(2017) for x in P.progsets[0].programs.values()}
# instructions = at.ProgramInstructions(alloc=alloc,start_year=2017)
# res3 = P.run_sim(parset=-1,progset=-1,progset_instructions=instructions,result_name='Half budget')
#
#
# d = at.PlotData(res1,outputs=':acj',pops={'Total':['0-14','15+','15+ HIV']}).interpolate(2025)
# d.series[0].vals
#
# d = at.PlotData(res_baseline,outputs=':acj',pops={'Total':['0-14','15+','15+ HIV']}).interpolate(2025)
# d.series[0].vals
#
# d = at.PlotData([res1,res2,res3],outputs=':acj',pops={'Total':['0-14','15+','15+ HIV']})
# at.plot_series(d,axis='results')
#
# def get_val(result):
#     d = at.PlotData(result, outputs=':acj', pops={'Total': ['0-14', '15+', '15+ HIV']}).interpolate(2025)
#     return d.series[0].vals[0]
#
#
# # Fund programs one at a time
# zero_spend = {x.name:0 for x in P.progsets[0].programs.values()}
# instructions = at.ProgramInstructions(alloc=alloc,start_year=2017)
# res = P.run_sim(parset=-1,progset=-1,progset_instructions=instructions,result_name='No spending')
# reference = get_val(res)
#
# out = {}
# for prog in P.progsets[0].programs.values():
#     alloc = sc.dcp(zero_spend)
#     alloc[prog.name] = prog.spend_data.interpolate(2017)
#     print(alloc)
#     instructions = at.ProgramInstructions(alloc=alloc, start_year=2017)
#     res = P.run_sim(parset=-1, progset=-1, progset_instructions=instructions, result_name='No spending')
#     out[prog.name] = get_val(res)