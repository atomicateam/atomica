import atomica as at
import sciris as sc
import os

import xlrd

import atomica as at


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