"""
This file implements YAML calibration, a mechanism of programming multiple automated calibration steps
(and related operations). Essentially this scheme coordinates repeated calls to at.calibrate with different
adjustables and measurables in a pre-defined sequence of automated calibration steps.
"""

import sciris as sc
from pathlib import Path
import shutil
import atomica as at
import numpy as np
import yaml
import time
import re

__all__ = ['build', 'run']

from atomica import ParameterSet


def _get_named_nodes():
    """
    Return dictionary with all named Node subclasses
    """
    return {x._name: x for x in BaseNode.__subclasses__() if x._name is not None}

def build(instructions=None, context=None, name='calibration'):
    """
    Construct nodes representing a calibration

    :param instructions: A dictionary of attributes/settings defined for this node OR a string filename
                         containing a YAML file that can be loaded to provide instructions
    :param context: A dictionary of attributes/settings inherited from parent nodes
    :param name: The name to assign this node
    :param fname: Optionally read the instructions from a file
    :return: A Node subclass instance, the type of which depends on the instructions
    """

    if (sc.isstring(instructions) or isinstance(instructions, Path)) and Path(instructions).exists():
        with open(instructions) as file:
            instructions =  yaml.load(file, Loader=yaml.FullLoader)

    named_nodes = _get_named_nodes()
    if isinstance(instructions, dict) and ('adjustables' in instructions or (context is not None and 'adjustables' in context)) and ('measurables' in instructions or (context is not None and 'measurables' in context)):
        return CalibrationNode(instructions, context, name)
    elif name in named_nodes:
        return named_nodes[name](instructions, context, name)
    else:
        return SectionNode(instructions, context, name)

def run(node, project, parset, savedir=None, save_intermediate=False, log_output:bool=False,*args, **kwargs):
    """
    Run YAML calibration

    This will execute the YAML calibration using the passed-in node (or instructions to build a node), and any associated children

    :param node: Calibration node to execute. If not a node (i.e., a YAML file, or node instructions), it will be converted into a node
    :param P: Project to which to apply these instructions
    :param parset: An `at.ParameterSet` instance to calibrate
    :param savedir: Optionally specify a directory to save the results. Defaults to the current working directory
    :param save_intermediate: Set whether to save intermediate calibrations (defaults to False)
    :return new_parset: A calibrated `at.ParameterSet` instance
    """

    if savedir is None:
        savedir = Path('.')
    else:
        savedir = Path(savedir)
    savedir.mkdir(exist_ok=True, parents=True)

    if not isinstance(node, BaseNode):
        # Save a copy of the yaml-file if saving log output
        if isinstance(node, Path) and log_output:
            shutil.copyfile(node, savedir / node.name)
        node = build(node)

    parset = sc.dcp(project.parset(parset))

    nodes = list(node.walk()) # Make a flat list of all nodes to execute in order
    n_steps = len([x for x in nodes if not isinstance(x[1], SectionNode)])
    n = 1

    if log_output:
        at.start_logging(savedir/'calibration_log.txt')

    at.logger.info(f'\nStarting calibration ({n_steps} steps)')

    for n_reps, node in nodes:

        if isinstance(node, SectionNode):
            at.logger.info(f'\nSection "{node.name}" (repeat {n_reps} of {node.repeats})')
        else:
            at.logger.info(f'\nStep {n} of {n_steps}: "{node.name}" (repeat {n_reps} of {node.repeats})')
            parset = node.apply(project, parset, savedir, save_intermediate, *args, **kwargs)
            n += 1

            if save_intermediate and not isinstance(node, SaveCalibrationNode):
                output = savedir / f'intermediate_calibration_{n:0{len(str(n_steps))}}_{node.name.replace(" ", "_")}'
                at.logger.info(f'Saving intermediate calibration...')
                parset.save_calibration(output)

    t = time.process_time()
    at.logger.info(f'\nCalibration completed. Total time elapsed: {round(t, 2)} seconds ({round(t/60, 2)} minutes)')

    if log_output:
        at.stop_logging()

    return parset


class BaseNode:
    """
    Node base class

    The base node class implements basic node features. Typically there should not be any
    instances of this class, only instances of subclasses
    """

    _name = None  # If specified, this key can be used as the name of the step to create a node of this type

    def __init__(self, instructions, context, name):
        self.name = name
        self.instructions = sc.dcp(instructions)
        self.context = context  # Attributes inherited from parent nodes
        self.children = []
        self.validate()

    def walk(self):
        n_reps = 0
        for repeat in range(self.repeats):
            n_reps += 1
            yield (n_reps, self)
            for child in self.children:
                yield from child.walk()

    @property
    def n_steps(self):
        if type(self) == BaseNode:
            return self.repeats * sum(child.n_steps for child in self.children)
        else:
            return self.repeats

    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.name}" x{self.repeats}>'

    def __str__(self, indent=0):
        """
        Print a tree representation of this node and all children

        :param indent: Recursively increase the indent for child nodes
        :return:
        """
        s =  '\t' * indent + self.__repr__()
        for child in self.children:
            s += '\n' + child.__str__(indent=indent + 1)
        return s

    @property
    def attributes(self):
        return sc.mergedicts(self.context, self.instructions)

    def __getitem__(self, item):
        # Directly index the Node to extract attributes without merging the dictionaries every time
        if item in self.instructions:
            return self.instructions[item]
        elif item in self.context:
            return self.context[item]
        else:
            raise KeyError(item)

    def __setitem__(self, key, value):
        self.instructions[key] = value

    def __contains__(self, item):
        return item in self.instructions or item in self.context

    @property
    def repeats(self):
        # Although repeats may be part of the context, we only repeat a node if the instructions requested a repeat
        # i.e., repeats are not inherited
        if isinstance(self.instructions, dict) and 'repeats' in self.instructions:
            return self.instructions['repeats']
        else:
            return 1

    def validate(self):
        """
        Validate/sanitize contents of this node

        If the node isn't valid, an error should be raised
        """
        return

    def apply(self, project: at.Project, parset: at.ParameterSet, savedir, *args, **kwargs) -> ParameterSet:
        """
        Perform the action associated with this node
        """
        return parset

class SectionNode(BaseNode):
    """
    A section node is a special kind of node, that contains other nodes
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = self.make_children()
        self.validate()

    def make_children(self):

        children = []

        # Remove any keys in the instructions that correspond to named nodes
        # These should be used as instructions for the child node, rather than
        # forming part of the context that is passed down to all children
        named_nodes = _get_named_nodes()
        step_instructions = {k: v for k, v in self.instructions.items() if isinstance(v, dict) or k in named_nodes}
        for k in step_instructions:
            del self.instructions[k]

        # Create the child nodes
        for name, instructions in step_instructions.items():
            children.append(build(instructions, self.attributes, name))

        return children

class CalibrationNode(BaseNode):

    # Order for list of adjustable parameters and default values
    adj_defaults = {
        'lower_bound': 0.1,
        'upper_bound': 10.0,
        'initial_value': None,
    }

    # Order for list of measurable parameters and default values
    meas_defaults = {
        'weight': 1.0,
        'metric': 'fractional',
        'cal_start': -np.inf,
        'cal_end': np.inf,
    }

    @staticmethod
    def parse_list(l, defaults):
        # Routine to parse list of arguments into a dictionary of values
        d = {}
        #convert number strings back to numerical values
        for i, e in enumerate(l.copy()):
            try:
                l[i] = float(e)  
            except ValueError:
                pass

        for k, v in zip(list(defaults.keys())[:len(l)], l):
            d[k] = v
        return d

    def validate(self):
        """
        Pre-parse calibration inputs
        """

        def separate_keys(keys_str: str) -> list:
            """
            Separate inputs that kave been defined together as one key in the YAML file into a list of strnigs.
            """
            in_brackets = False
            brackets_str = ''
            nobrackets_str = ''
            separated_keys = []

            for ch in keys_str:
                if ch == '(':
                    in_brackets = True
                    continue
                elif ch == ')':
                    in_brackets = False
                    separated_keys.append(brackets_str)
                    brackets_str = ''
                    continue

                if in_brackets:
                    brackets_str += ch
                else:
                    if ch == ',':
                        if nobrackets_str == ' ' or nobrackets_str == '':
                            nobrackets_str = ''
                            continue
                        else:
                            separated_keys.append(nobrackets_str)
                            nobrackets_str = ''
                    else:
                        nobrackets_str += ch

            if nobrackets_str != '' and nobrackets_str != ' ':
                separated_keys.append(nobrackets_str)

            return [x.strip() for x in separated_keys]

        def process_key(key: str) -> tuple:
            """
            Sanitize key name, separating optional pop name/s from par name
            #TODO add example and further explanation
            """
            if ',' in key:
                return tuple([x.strip() for x in key.strip('() ').split(',') if x])
            else:
                return (key.strip(), None)

        def process_list(l) -> (str,list):
            """description"""
            if len(l) == 1:
                #if the list is already just one string, return that string as key with None pop and vals
                return (l[0].strip('() '), None), None
            elif '(' in str(l):
                # separate out the parenthesis contents as the par/pop/s,
                # then output the key (par, pop tuple) and value

                # process keys
                s = str(l).strip("[] ").replace("'", "")
                s1 = re.findall(r'\(.*?\)', s)
                key = process_key(s1[0].replace('(', '').replace(')', ''))

                # process values/settings
                value = s.replace(s1[0], '').strip(', ').split(',')
                value = [x.strip(', ') for x in value if x]
                return key, value
            else:
                key = process_key(l[0])
                value = l[1:]
                return key, value

        def process_inputs(inputs, defaults):
            """
            Process adjustables and measurables, which can be specified in a list representation or nested dict representation
            In list representation, the input is a list of lists, where the first item in each list is the quantity (with optional population) and
            the remaining items are the supported arguments for the input type, in the order defined by the defaults dictionary.
            In a dict representation, the key is the quantity with optional population, and then the value can either be a list (in the order defined by the dictionary)
            or a dictionary explicitly naming the inputs.
            This function returns a flat dictionary with {(quantity, pop_name):{argument:value}} e.g., {('b_rate','0-5'):{'lower_bound':0.5}}.
            In the dict representation, the key can be a comma separated list of quantities with optional values e.g., 'b_rate 0-5, d_rate'. In the list representation,
            multiple quantities are not supported (as a comma is already used to separate the arguments), but multiple lists (one for each quantity) can be provided.
            """
            out = {}

            if sc.isstring(inputs):
                # Support a comma separated string with "quantity pop" specifications of adjustables and measurables
                # In this case, default values should be used for all other items. Proceed by splitting into a list
                inputs = inputs.split(',')

            if isinstance(inputs, (tuple, list)):
                for l in inputs:
                    l = sc.promotetolist(l)
                    keyspops, v = process_list(l)
                    
                    #process key
                    if len(keyspops) == 2:
                        key, pop_name = keyspops
                    else:
                        assert len(keyspops) == 3, f'Number of populations must be 0, 1 or 2.'
                        key = f'{keyspops[0]}_from_{keyspops[1]}'
                        pop_name = keyspops[2]

                    #process value
                    if v is None:
                        value = defaults
                    else:
                        value = self.parse_list(v, defaults)

                    out[key, pop_name] = sc.mergedicts(out.get((key, pop_name), {}), value)

            elif isinstance(inputs, dict):
                for keys, v in inputs.items():

                    separated_keys = separate_keys(keys)
                    for key in separated_keys:
                        #separate par name from pop name
                        keyspops = process_key(key.strip())
                        if len(keyspops) == 2:
                            key, pop_name = keyspops
                        else:
                            assert len(keyspops) == 3, f'Number of populations must be 0, 1 or 2.'
                            key = f'{keyspops[0]}_from_{keyspops[1]}'
                            pop_name = keyspops[2]

                        #process values
                        if isinstance(v, (tuple, list)):
                            value = self.parse_list(v, defaults)
                        else:
                            value = v.copy()

                        #add keys and values to outputs dict
                        out[key, pop_name] = sc.mergedicts(out.get((key, pop_name), {}), value)
            return out

        self['adjustables'] = process_inputs(self['adjustables'], self.adj_defaults)
        self['measurables'] = process_inputs(self['measurables'], self.meas_defaults)

        def check_optional_number(key, v, defaults):
            if key in v and v[key] is not None:
                if not sc.isnumber(v[key], isnan=False):
                    raise TypeError(f"Adjustable argument {key} needs to be a number or None (defaults to {defaults[key]}). Provided value: {v[key]} ")

        # Validate adjustables
        assert len(self['adjustables']) > 0, f'Cannot calibrate with no adjustables for calibration section {self.name}'
        for (quantity, pop_name), v in self['adjustables'].items():
            assert 'pop_name' not in v, f'Setting the population name through "pop_name: {v["pop_name"]}" is not supported. Instead, the name of the adjustable quantity should include the population name ("{quantity} {v["pop_name"]}")'
            assert isinstance(quantity, str), f'Adjustable codename {quantity} needs to be a string'
            assert pop_name is None or isinstance(pop_name, str), f'Adjustable population {pop_name} needs to be a string or None (defaults to all populations for that parameter)'
            check_optional_number('lower_bound',v, self.adj_defaults)
            check_optional_number('upper_bound',v, self.adj_defaults)
            check_optional_number('initial_value',v, self.adj_defaults)

        # Validate measurables
        assert len(self['measurables']) > 0, f'Cannot calibrate with no measurables for calibration section {self.name}'
        for (quantity, pop_name), v in self['measurables'].items():
            assert isinstance(quantity, str), f'Measurable codename {quantity} needs to be a string'
            assert pop_name is None or isinstance(pop_name, str), f'Adjustable population {pop_name} needs to be a string or None (defaults to all populations for that parameter)'
            assert 'metric' not in v or v['metric'] is None or isinstance(v["metric"], str), f"Measurable metric {v['metric']} needs to be a number or None (defaults to 'fractional')"

            check_optional_number('weight',v, self.meas_defaults)
            check_optional_number('cal_start',v, self.meas_defaults)
            check_optional_number('cal_end',v, self.meas_defaults)

    def apply(self, project: at.Project, parset: at.ParameterSet, n: int, *args, quiet=False, compare_results=False, **kwargs) -> ParameterSet:

        step_name = self.name
        attributes = self.attributes

        at.logger.info(f"Calibrating adjustable(s) {set([adj[0] for adj in attributes['adjustables']])} to match measurable(s) {set([mea[0] for mea in attributes['measurables']])}...")

        # Expand adjustables
        adjustables = {}
        par_names = {x[0] for x in attributes['adjustables']}.intersection(x.name for x in parset.all_pars())
        pop_names = {x[1] for x in attributes['adjustables']}.intersection({*parset.pop_names} | {'all', None})

        adj_defaults = {k:self.attributes[k] if k in self.attributes else self.adj_defaults[k] for k in self.adj_defaults}

        for par_name, pop_name in attributes['adjustables']:

            if par_name not in par_names:
                at.logger.warning(f"Extra YAML adjustable parameter '{par_name}' does not exist in this project's framework/parset and will be ignored")
                continue
            elif pop_name not in pop_names:
                at.logger.warning(f"Extra YAML adjustable population '{pop_name}' does not exist in this project's databook and will be ignored")
                continue

            if pop_name is None:
                pops = parset.pop_names
            else:
                pops = sc.promotetolist(pop_name)

            for pop in pops:
                d = sc.mergedicts(adj_defaults,  attributes['adjustables'].get((par_name, None), None),  attributes['adjustables'].get((par_name, pop), None))
                adjustables[(par_name, pop)] = (d['lower_bound'], d['upper_bound'], d['initial_value'])
        adjustables = [(*k, *v) for k,v in adjustables.items()]


        # Expand measurables
        measurables = {}
        par_names = {x[0] for x in attributes['measurables']}.intersection(x.name for x in parset.all_pars())  # TODO: This is probably OK for now but will need to validate that pars have databook entries in the future
        pop_names = {x[1] for x in attributes['measurables']}.intersection({*parset.pop_names} | {None})

        meas_defaults = {k: self.attributes[k] if k in self.attributes else self.meas_defaults[k] for k in self.meas_defaults}

        for par_name, pop_name in attributes['measurables']:

            if par_name not in par_names:
                at.logger.warning(f"Extra YAML measurable variable '{par_name}' does not exist in this project's framework and will be ignored")
                continue
            elif pop_name not in pop_names:
                if not (pop_name.lower() == 'total' and pop_name.lower() in {x.lower() for x in project.data.tdve[par_name].ts.keys()}):
                    at.logger.warning(f"Extra YAML measurable population '{pop_name}' does not exist in this project's databook and will be ignored")
                    continue

            if pop_name is None:
                pops = parset.pop_names
            else:
                pops = sc.promotetolist(pop_name)

            for pop in pops:
                d = sc.mergedicts(meas_defaults,  attributes['measurables'].get((par_name, None), None), attributes['measurables'].get((par_name, pop), None))
                measurables[(par_name, pop)] = (d['weight'], d['metric'], d['cal_start'], d['cal_end'])
        measurables = [(*k, *v) for k,v in measurables.items()]

        # Calibration
        if len(adjustables):
            # note: attributes = instructions + context
            kwargs = sc.mergedicts(self.attributes, kwargs)

            del kwargs['adjustables'] # supplied via the adjustables variable
            del kwargs['measurables'] # supplied via the measurables variable

            if 'repeats' in kwargs:
                del kwargs['repeats']

            if quiet:
                with at.Quiet(show_warnings=False):
                    new_cal_parset = at.calibrate(project, parset, adjustables, measurables, **kwargs)
            else:
                new_cal_parset = at.calibrate(project, parset, adjustables, measurables, **kwargs)
        else:
            new_cal_parset = parset

        at.logger.info(f'Completed "{step_name}"...')
        made_changes = False

        for par, pop, *_ in adjustables:

            if pop == "all":
                old = parset.get_par(par).meta_y_factor
                new = new_cal_parset.get_par(par).meta_y_factor
            else:
                old = parset.get_par(par).y_factor[pop]
                new = new_cal_parset.get_par(par).y_factor[pop]

            if new != old:
                at.logger.info(f'...adjusted the y-factor for {par} in {pop} from {old} to {new}')
                made_changes = True
            else:
                at.logger.debug(f'...did NOT adjust the y-factor for {par} in {pop} from {old} to {new}')

        if not made_changes:
            at.logger.info(f'...made no changes!')

        if compare_results:
            base_res = project.run_sim(parset=parset)
            cal_res = project.run_sim(parset=new_cal_parset)
            for par_name in [par_measure[0] for par_measure in measurables]:
                base_rms_error = 0
                cal_rms_error = 0
                for pop in parset.pars[par_name].ts.keys():
                    for time_par_ind, time_value in enumerate(parset.pars[par_name].ts[pop].t):
                        data_time_val = parset.pars[par_name].ts[pop].vals[time_par_ind]
                        base_res_time_ind = list(base_res.get_variable(par_name, pop)[0].t).index(time_value)
                        base_time_val = base_res.get_variable(par_name, pop)[0].vals[base_res_time_ind]
                        cal_res_time_ind = list(cal_res.get_variable(par_name, pop)[0].t).index(time_value)  # probably redundant as they *should* be the same
                        cal_time_val = cal_res.get_variable(par_name, pop)[0].vals[cal_res_time_ind]

                        base_rms_error += (data_time_val - base_time_val) ** 2
                        cal_rms_error += (data_time_val - cal_time_val) ** 2

                        sf = at.get_sigfigs_necessary(base_time_val, cal_time_val)
                        at.logger.info(f'...for parameter {par_name} and population {pop} at time {time_value} the data value was {sc.sigfig(data_time_val, sf)}, the baseline value was {sc.sigfig(base_time_val, sf)}, and the calibrated value was {sc.sigfig(cal_time_val, sf)}.')

                base_rms_error = base_rms_error ** 0.5
                cal_rms_error = cal_rms_error ** 0.5
                sf = at.get_sigfigs_necessary(base_rms_error, cal_rms_error)
                at.logger.info(f'...RMS error for parameter {par_name} has changed from baseline {sc.sigfig(base_rms_error, sf)} to calibrated {sc.sigfig(cal_rms_error, sf)}')

        return new_cal_parset


class InitializationNode(BaseNode):
    _name = 'set_initialization'

    def __init__(self, instructions, context, name ):
        new_instructions = {}

        if isinstance(instructions, dict):
            new_instructions.update(instructions)
        elif type(instructions) is int:
            new_instructions.update({'init_year': instructions})
        elif isinstance(instructions, (tuple, list)):
            sc.promotetolist(instructions)
            new_instructions.update({'init_year': instructions[0]})
            if len(instructions) > 1:
                new_instructions.update({'constant_parset': instructions[1]})

        super().__init__(new_instructions, context, name)

    def validate(self):
        assert 'init_year' in self, f'Initialization year must be specified'
        assert sc.isnumber(self['init_year']), f'Initialization year {self["init_year"]} must be numeric.'
        if 'constant_parset' in self:
            assert isinstance(self['constant_parset'], int), f'Constant parset (optional) {self["constant_parset"]} must be numeric (boolean, or int to specify constant parset year).'

    def apply(self, project: at.Project, parset: at.ParameterSet, n: int, *args, **kwargs) -> ParameterSet:
        p2 = sc.dcp(parset)
        if 'constant_parset' in self:
            if self['constant_parset'] == True:
                p2 = parset.make_constant(year=project.settings.sim_start)
            elif type(self['constant_parset']) == int: #constant parset year was provided
                p2 = parset.make_constant(year=self['constant_parset'])
        new_settings = sc.dcp(project.settings)
        new_settings.update_time_vector(end=self['init_year'])
        res = at.run_model(settings=new_settings, framework=project.framework, parset=p2)
        parset.set_initialization(res, self['init_year'])
        return parset


class ClearInitializationNode(BaseNode):
    _name = 'clear_initialization'

    def __init__(self, instructions, context, name):
        super().__init__(instructions=None, context=context, name=name)

    def apply(self, project: at.Project, parset: at.ParameterSet, n: int, *args, **kwargs) -> ParameterSet:
        parset.initialization = None
        return parset


class SaveCalibrationNode(BaseNode):
    """
    Block in YAML file with "save calibration: <file name>"
    """

    _name = 'save_calibration'

    def __init__(self, instructions, context, name):
        if not isinstance(instructions, dict):
            instructions = {'fname': instructions}
        super().__init__(instructions, context, name)

    def validate(self):
        assert self['fname'] is not None, 'A "save calibration" node must have a file name explicitly specified'

    def apply(self, project: at.Project, parset: at.ParameterSet, savedir=None, *args, **kwargs) -> ParameterSet:
        parset.save_calibration(savedir / self['fname'])
        return parset
