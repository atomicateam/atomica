"""
Define classes and functions for handling scenarios
Version: 2018mar26
"""

import numpy as np
import sciris.core as sc
from .system import AtomicaException, logger
from .utils import NamedItem
from .programs import ProgramInstructions

class Scenario(NamedItem):
    def __init__(self, name):
        NamedItem.__init__(self, name)
        self.result_uid = None # If the scenario is run via Project.run_scenario, this will be the UID of the most recent result generated using this Scenario

    def get_parset(self, parset, settings):
        return parset

    def get_progset(self, progset, settings, options):
        return progset, options


class ParameterScenario(Scenario):
    def __init__(self, name, scenario_values=None):
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

        new_parset = sc.dcp(parset)

        for par_label in self.scenario_values.keys():
            par = new_parset.get_par(par_label)  # This is the parameter we are updating

            for pop_label, overwrite in self.scenario_values[par_label].items():

                if not par.has_values(pop_label):
                    raise AtomicaException("You cannot specify overwrites for a parameter with a function, instead you should overwrite its dependencies")

                original_y_end = par.interpolate(np.array([max(overwrite['t']) + 1e-5]), pop_label)

                # If the Parameter had an assumption, then expand the assumption out first
                if len(par.t[pop_label]) == 1 and np.isnan(par.t[pop_label][0]):
                    par.t[pop_label] = np.array([settings.sim_start, settings.sim_end])
                    par.y[pop_label] = par.y[pop_label] * np.ones(par.t[pop_label].shape)

                if 'smooth_onset' not in overwrite:
                    overwrite['smooth_onset'] = 1e-5

                if np.isscalar(overwrite['smooth_onset']):
                    onset = np.zeros((len(overwrite['y']),))
                    onset[0] = overwrite['smooth_onset']
                else:
                    assert len(overwrite['smooth_onset']) == len(overwrite['y']), 'Smooth onset must be either a scalar or an array with length matching y-values'
                    onset = overwrite['smooth_onset']

                # Now, insert all of the program overwrites
                if len(overwrite['t']) != len(overwrite['y']):
                    raise AtomicaException('Number of time points in overwrite does not match number of values')

                if len(overwrite['t']) == 1:
                    logger.warning('Only one time point was specified in the overwrite, which means that the overwrite will not have any effect')

                for i in range(0, len(overwrite['t'])):

                    # Account for smooth onset
                    if onset[i] > 0:
                        t = overwrite['t'][i] - onset[i]

                        if i > 0 and t > overwrite['t'][i - 1]:
                            # If the smooth onset extends to before the previous point, then just use the
                            # previous point directly instead
                            y = overwrite['y'][i - 1] / par.y_factor[pop_label]
                            par.remove_between([overwrite['t'][i - 1], overwrite['t'][i]], pop_label)
                            par.insert_value_pair(t, y, pop_label)
                        else:
                            # Otherwise, get the value at the smooth onset time, add it as a control
                            # point, and remove any intermediate points
                            y = par.interpolate(np.array([t]), pop_label)
                            par.remove_between([t, overwrite['t'][i]], pop_label)  # Remove values during onset period
                            par.insert_value_pair(t, y, pop_label)
                    elif i > 0:
                        # If not doing smooth onset, and this is not the first point being overwritten,
                        # then remove all control points between this point and the last one
                        par.remove_between([overwrite['t'][i - 1], overwrite['t'][i]], pop_label)

                    # Insert the overwrite value - assume scenario value is AFTER y-factor rescaling
                    par.insert_value_pair(overwrite['t'][i], overwrite['y'][i] / par.y_factor[pop_label], pop_label)

                # Add an extra point to return the parset back to it's original value after the final overwrite
                par.insert_value_pair(max(overwrite['t']) + 1e-5, original_y_end, pop_label)

            new_parset.name = self.name + '_' + parset.name
            return new_parset

class BudgetScenario(Scenario):

    def __init__(self, name=None, active=True, parsetname=None, progsetname=None, alloc=None, start_year=None, verbose=False):
        if verbose: print('Creating budget scenario with name=%s, parsetname=%s, progsetname=%s, start_year=%s' % (name, progsetname, parsetname, start_year))
        self.name = name
        self.active = active  # whether the scenario is active or not
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.alloc = alloc
        self.start_year = start_year
        return None
    
    def run(self, project=None):
        instructions = ProgramInstructions(alloc=self.alloc, start_year=self.start_year) # Instructions for default spending
        result = project.run_sim(parset=self.parsetname, progset=self.progsetname, progset_instructions=instructions, result_name=self.name)
        return result


#
#
# class CoverageScenario(BudgetScenario):
#
#     def __init__(self, name, scenario_values=None, **kwargs):
#         super(CoverageScenario, self).__init__(name, scenario_values=scenario_values)
#
#     def get_progset(self, progset, settings, options):
#         progset, options = super(CoverageScenario, self).get_progset(progset, options)
#         options['alloc_is_coverage'] = True
#         return progset, options
