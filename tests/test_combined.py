import atomica as at
import sciris as sc
import os
import numpy as np

import xlrd

import atomica as at

def test_creation():
    F = at.ProjectFramework(at.LIBRARY_PATH+'combined_framework.xlsx')
    pops = {
        'SIR1':{'label':'SIR 1','type':'sir'},
        'SIR2': {'label': 'SIR 2', 'type': 'sir'},
        'SIR3': {'label': 'SIR 3', 'type': 'sir'},
        'UDT1': {'label': 'UDT 1', 'type': 'udt'},
        'UDT2': {'label': 'UDT 2', 'type': 'udt'},
        }

    transfers = {
        'aging_sir': {'label': 'Aging SIR', 'type': 'sir'},
        'aging_udt': {'label': 'Aging UDT', 'type': 'udt'},
        }

    D = at.ProjectData.new(framework=F,tvec=[2016,2017,2018],pops=pops,transfers=transfers)
    D.save('combined_test.xlsx')
    D2 = at.ProjectData.from_spreadsheet('combined_test.xlsx',framework=F)
    D2.add_pop('UDT3','UDT 3','udt')
    D2.add_transfer('incarceration','Incarceration','sir')
    D2.save('combined_test2.xlsx')

    D3 = at.ProjectData.from_spreadsheet('combined_test.xlsx',framework=F) # Load in the original one because it has no missing values
    D3.validate(F)

    P = at.Project(framework=F,databook='combined_test.xlsx')

    ps = at.ProgramSet.new('default',tvec=np.arange(2015,2019),progs=9,project=P)
    ps.save('combined_progbook_test.xlsx')

    ps2 = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH+'combined_progbook.xlsx',project=P)
    ps2.add_program('test','test')
    ps2.save('combined_added.xlsx')

def test_demo_values():
    P1 = at.demo('sir',do_run=False)
    P1.settings.update_time_vector(start=2016,end=2021)
    R1 = P1.run_sim('default')
    P2 = at.demo('udt',do_run=False)
    P2.settings.update_time_vector(start=2016,end=2021)
    R2 = P2.run_sim('default')
    P3 = at.demo('combined',do_run=False)
    P3.settings.update_time_vector(start=2016,end=2021)
    R3 = P3.run_sim('default')



    R1.model.pops[0].get_comp('sus').vals
    R3.model.pops[0].get_comp('sus').vals

    R2.model.pops[0].get_comp('undx').vals
    R3.model.pops[3].get_comp('undx').vals

def test_demo():
    P = at.demo('combined',do_run=False)
    R = P.run_sim('default')

if __name__ == "__main__":
    # test_creation()
    test_demo_values()
    # test_demo()