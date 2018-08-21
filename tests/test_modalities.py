# Simple modalities test
import atomica as au
from atomica.programs import Covout
import sciris as sc

## This is the 3-program case on the first sheet of `cost_function_test.xlsx`
progs = ['HTC clinics','HTC outreach','HTC home test']
coverage = [0.244945,0.022795,0.056632]
outcome = [0.8,0.9,0.4]
baseline = 0.3

## This is the 4-program case on the second sheet
progs = ['P1','P2','P3','P4']
coverage = [0.2,0.15,0.3,0.1]
outcome = [50,40,20,80]
baseline = 5

covout = Covout('testing_rate',
                'adults',
                cov_interaction='random',
                imp_interaction='best',
                baseline=baseline,
                progs={prog:val for prog,val in zip(progs,outcome)}
                )


covout.cov_interaction = 'additive'
final = covout.get_outcome({prog:sc.promotetoarray(val) for prog,val in zip(progs,coverage)})
print(final)

covout.cov_interaction = 'random'
final = covout.get_outcome({prog:sc.promotetoarray(val) for prog,val in zip(progs,coverage)})
print(final)

covout.cov_interaction = 'nested'
final = covout.get_outcome({prog:sc.promotetoarray(val) for prog,val in zip(progs,coverage)})
print(final)