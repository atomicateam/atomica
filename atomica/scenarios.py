'''
Define classes and functions for handling scenarios
Version: 2018mar26
'''

### Imports
#from numpy import append, array, inf
#from optima import AtomicaException, Multiresultset # Core classes/functions
#from optima import dcp, today, findinds, vec2obj, isnumber, promotetoarray # Utilities
from atomica.system import AtomicaException
from sciris.core import defaultrepr, printv, odict, Link # TODO - replace utilities imports
import numpy as np
from copy import deepcopy as dcp

class Scenario(object):

    def __init__(self, name):
        self.name = name

    def get_parset(self, parset, settings):
        return parset

    def get_progset(self, progset, settings, options):
        return progset, options

    def __repr__(self):
        return '%s "%s"' % (self.__class__.__name__, self.name)

class ParameterScenario(Scenario):

    def __init__(self, name, scenario_values=None, **kwargs):
        """
        Given some data that describes a parameter scenario, creates the corresponding parameterSet
        which can then be combined with a ParameterSet when running a model.

        Params:
            scenario_values:     list of values, organized such to reflect the structure of a linkpars structure in data
                                 data['linkpars'] = {parameter_label : {pop_label : odict o }  where
                                     o = dict/odict with keys:
                                         t : np.array or list with year values
                                         y : np.array or list with corresponding parameter values


        Example:
            scvalues = dict()
            param = 'birth_transit'
            scvalues[param] = dict()
            scvalues[param]['Pop1'] = dict()
            scvalues[param]['Pop1']['y'] = [3e6, 1e4, 1e4, 2e6]
            scvalues[param]['Pop1']['t'] = [2003.,2004.,2014.,2015.]

            OPTIONALLY can also specify
            scvalues[param]['Pop1']['smooth_onset'] = 1
            scvalues[param]['Pop1']['smooth_onset'] = [1,2,3,4] (same length as y)

            pscenario = ParameterScenario(name="examplePS",scenario_values=scvalues)

        """
        super(ParameterScenario, self).__init__(name)
        # TODO - could do some extra validation here
        self.scenario_values = scenario_values

    def get_parset(self, parset, settings):
        """
        Get the corresponding parameterSet for this scenario, given an input parameterSet for the default baseline
        activity.

        The output depends on whether to overwrite (replace) or add values that appear in both the
        parameterScenario's parameterSet to the baseline parameterSet.
        """

        # Note - the parset will be overwritten between the first and last year specified in scvalues
        # on a per-parameter+pop basis. Within the scenario, only the data points in scvalues will be used

        new_parset = dcp(parset)

        for par_label in self.scenario_values.keys():
            par = new_parset.get_par(par_label)  # This is the parameter we are updating

            for pop_label, overwrite in self.scenario_values[par_label].items():

                original_y_end = par.interpolate(np.array([max(overwrite['t'])+1e-5]), pop_label)

                if len(par.t[pop_label]) == 1 and np.isnan(par.t[pop_label][0]):
                    par.t[pop_label] = np.array([settings.sim_start,settings.sim_end])
                    par.y[pop_label] = par.y[pop_label]*np.ones(par.t[pop_label].shape)

                if 'smooth_onset' not in overwrite:
                    overwrite['smooth_onset'] = 1e-5

                if np.isscalar(overwrite['smooth_onset']):
                    onset = np.zeros((len(overwrite['y']),))
                    onset[0] = overwrite['smooth_onset']
                else:
                    assert len(overwrite['smooth_onset']) == len(overwrite['y']), 'Smooth onset must be either a scalar or an array with length matching y-values'
                    onset = overwrite['smooth_onset']

                # Now, insert all of the program overwrites
                for i in range(0, len(overwrite['t'])):

                    # Account for smooth onset
                    if onset[i] > 0:
                        t = overwrite['t'][i] - onset[i]
                        if i == 0:
                            y = par.interpolate(np.array([t]), pop_label) # Interpolation does not rescale, so don't worry about it here
                        else:
                            y = overwrite['y'][i-1]
                        par.insertValuePair(t, y, pop_label)

                        # Remove any intermediate values which are now smoothed via interpolation
                        par.removeBetween([t, overwrite['t'][i]], pop_label)

                    # Insert the overwrite value - assume scenario value is AFTER y-factor rescaling
                    par.insertValuePair(overwrite['t'][i], overwrite['y'][i] / par.y_factor[pop_label], pop_label)

            # Add an extra point
            par.insertValuePair(overwrite['t'][i]+1e-5, original_y_end, pop_label)

            new_parset.name = self.name + '_' + parset.name
            return new_parset


class BudgetScenario(Scenario):

    def __init__(self, name, scenario_values=None, **kwargs):
        super(BudgetScenario, self).__init__(name)
        self.makeScenarioProgset(budget_allocation=scenario_values)
        self.budget_allocation = budget_allocation

    def get_progset(self, progset, settings, budget_options):
        """
        Get the updated program set and budget allocation for this scenario.
        This combines the values in the budget allocation with the values for the scenario.

        Note that this assumes that all other budget allocations that are NOT
        specified in budget_options are left as they are.

        Params:
            progset            program set object
            budget_options     budget_options dictionary
        """
        new_budget_options = dcp(budget_options)
        if self.overwrite:
            for prog in self.budget_allocation.keys():
                new_budget_options['init_alloc'][prog] = self.budget_allocation[prog]

        else:  # we add the amount as additional funding
            for prog in self.budget_allocation.keys():

                if new_budget_options['init_alloc'].has_key(prog):
                    new_budget_options['init_alloc'][prog] += self.budget_allocation[prog]
                else:
                    new_budget_options['init_alloc'][prog] = self.budget_allocation[prog]

        return progset, new_budget_options


class CoverageScenario(BudgetScenario):

    def __init__(self, name, scenario_values=None, **kwargs):
        super(CoverageScenario, self).__init__(name, scenario_values=scenario_values)

    def get_progset(self, progset, settings, options):
        progset, options = super(CoverageScenario, self).get_progset(progset, options)
        options['alloc_is_coverage'] = True
        return progset, options


