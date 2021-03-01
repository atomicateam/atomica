"""
Manage Project versions and migration

Migration refers to updating old :class:`Project` instances so that they
can be run with more recent versions of Atomica. This module defines

- A set of 'migration functions' that each transform a :class:`Project` instance from one
  version to another
- An entry-point that sequentially calls the migration functions to update a project to
  the current version used in Atomica

"""

import sys
import io
from distutils.version import LooseVersion
from .system import logger
from .version import version, gitinfo
import sciris as sc
from .system import FrameworkSettings as FS
import atomica
import types
import numpy as np
import pandas as pd
from collections import defaultdict
import pathlib
import os

__all__ = ["migration", "migrate", "register_migration"]

SKIP_MIGRATION = False  # Global migration flag to disable migration

# MODULE MIGRATIONS
#
# In this section, make changes to the Atomica module structure to enable pickle files
# to be loaded at all

# On Windows, pathlib.PosixPath is not implemented which can cause problems when unpickling
# Therefore, we need to turn PosixPath into WindowsPath on loading. The reverse is true on
# Unix systems
if os.name == "nt":
    pathlib.PosixPath = pathlib.WindowsPath
else:
    pathlib.WindowsPath = pathlib.PosixPath


class _Placeholder:
    pass


# First, add any placeholder modules that have been subsequently removed
atomica.structure = types.ModuleType("structure")  # Removed 'structure' module in 1.0.12 20181107
sys.modules["atomica.structure"] = atomica.structure

# Then, remap any required classes
atomica.structure.TimeSeries = atomica.utils.TimeSeries  # Moved 'TimeSeries' in 1.0.12 20181107

# If classes have been removed, then use the Placeholder class to load them
# The migration function can then replace Placeholder instances with actual
# instances - see the AtomicaSpreadsheet -> sciris.Spreadsheet migration function
atomica.excel.AtomicaSpreadsheet = _Placeholder
atomica.optimization.OptimInstructions = _Placeholder

# PROJECT MIGRATIONS
#
# The remaining code manages upgrading Project objects and their contents after they
# have been unpickled and instantiated

# This dict stores the migrations associated with each versioned class
# We migrate projects and results separately because they might be stored
# separately e.g. in a database


class Migration:
    """Class representation of a migration

    This class stores a migration function together with all required metadata. It would
    normally be instantiated using the `migration` decorator, which also registers the
    migration by adding it to the `migrations` list

    """

    def __init__(self, classname, original_version, new_version, description, fcn, date=None, update_required=False):
        """

        :param original_version:
        :param new_version:
        :param description:
        :param fcn:
        :param date:
        :param update_required: Flag if dependent content in the object might change e.g. if redoing a calculation might produce different results
        """
        self.classname = classname
        self.original_version = original_version
        self.new_version = new_version
        self.description = description
        self.update_required = update_required
        self.date = date
        self.fcn = fcn

    def upgrade(self, obj):
        logger.debug("MIGRATION: Upgrading %s %s -> %s (%s)" % (self.classname, self.original_version, self.new_version, self.description))
        obj = self.fcn(obj)  # Run the migration function
        if obj is None:
            raise Exception("%s returned None, it is likely missing a return statement" % (str(self)))
        obj.version = self.new_version  # Update the version
        if self.update_required:
            obj._update_required = True
        return obj

    def __repr__(self):
        return f"Migration({self.classname}, {self.original_version}->{self.new_version})"


def register_migration(registry, classname, original_version, new_version, description, date=None, update_required=False):
    """Decorator to register migration functions

    This decorator constructs a `Migration` object from a decorated migration function, and registers it
    in the module's list of migrations to be run when calling migrate()

    :param registry: Dictionary storing {classname:[migrations]}
    :param original_version: Version string for the start version. Function will only run on projects whose version is <= this
    :param new_version: The resulting project is assigned this version
    :param description: A brief overview of the purpose of this migration
    :param date: Optionally specify the date when this migration was written
    :param update_required: Optionally flag that changes to model output may occur - the flag is stored in the object's `_update_required` attribute.
                            Objects can optionally contain this attribute, so it's not necessary if the object is planned not to require
                            such a flag.
    :return: None

    Example usage::

        @migration('Project','1.0.0', '1.0.1', 'Upgrade project', update_required=True)
        def _update_project(proj):
            ...
            return proj

    The migration function (update_project()) takes a single argument which is a project object, and returns
    a project object. Decorating the function registers the migration and it will automatically be used by
    migrate() and therefore Project.load()

    """

    def register(f):
        if classname not in registry:
            registry[classname] = []
        registry[classname].append(Migration(classname, original_version, new_version, description, fcn=f, date=date, update_required=update_required))
        return f

    return register


migrations = dict()  # Registry of migrations in Atomica


def migration(*args, **kwargs):
    # Wrapper decorator to bind register_migration to the migration registry in this module
    return register_migration(migrations, *args, **kwargs)


def migrate(obj, registry=migrations, version=version, gitinfo=gitinfo):
    """Update a object to the latest version

    Run all of the migrations in the list of available migrations. The migrations are run in ascending order, as long
    as the version is <= the migration's original version. This way, migrations don't need to be added if a version number
    change takes place without actually needing a migration - instead, when adding a migration, just use whatever version
    numbers are appropriate at the time the change is introduced, it will behave sensibly.

    Typically, this function would not be called manually - it happens automatically as part of `Project.load()`.

    Note that this function returns the updated object. Typically the migration functions will update a
    object in-place, but this syntax allows migrations to replace parts of the object (or the entire object)
    if that is ever necessary in the future. So do not rely on `migrate` having side-effects, make sure the
    returned object is retained. In principle we could dcp() the object to ensure that only the
    copy gets migrated, but at this point it does not appear worth the performance overhead (since migration at the
    moment is only ever called automatically).

    :param proj: object to migrate
    :param version: The current version (in case this is reused in a separate module, defaults to Atomica's)
    :param gitinfo: The gitinfo to update (in case this is reused in a separate module, defaults to Atomica's)
    :return: Updated object

    """

    if type(obj).__name__ not in registry:
        return obj  # If there are no migrations for the object, then return immediately

    elif not hasattr(obj, "version"):
        # If the object has no version attribute, then add one with version 0. This is presumably
        # because the original object didn't have a version, but now migrations for it are required.
        # In that case, any object that doesn't have a version would require all migrations to be run.
        # New objects would all have a version already. After any migrations are run, these values will
        # then be updated to the current version
        obj.version = "0.0.0"
        obj.gitinfo = None

    if SKIP_MIGRATION:
        print("Skipping migration")
        return obj  # If migration is disabled then don't make any changes EXCEPT to add in version and gitinfo which may otherwise be hard to catch

    migrations_to_run = sorted(registry[type(obj).__name__], key=lambda m: LooseVersion(m.original_version))
    if sc.compareversions(obj.version, version) >= 0:
        return obj
    else:
        if hasattr(obj, "name"):
            logger.info('Migrating %s "%s" from %s->%s', type(obj).__name__, obj.name, obj.version, version)
        else:
            logger.info("Migrating %s from %s->%s", type(obj).__name__, obj.version, version)

    for m in migrations_to_run:  # Run the migrations in increasing version order
        if sc.compareversions(obj.version, m.new_version) < 0:
            obj = m.upgrade(obj)

    obj.version = version  # Set object version to the current Atomica version
    obj.gitinfo = gitinfo  # Update gitinfo to current version
    if hasattr(obj, "_update_required") and obj._update_required:
        logger.warning("Caution: due to migration, object may behave different if re-run.")
    return obj


def all_results(proj):
    """Helper generator to iterate over all results in a project

    Project results may be
        - Standalone results
        - A list of results
        - A UID string (that should be ignored)

    This function is a generator that allows iteration over all results in a project

    :param proj: A Project object
    :return: A Result (via yield)

    Example usage:

    for result in all_results(proj):
        do_stuff(result)

    """
    from .results import Result

    for result in proj.results.values():
        if isinstance(result, list):
            for r in result:
                yield r
        elif isinstance(result, Result):
            yield result


def all_progsets(proj):
    """Helper generator to iterate over all progsets in a project

    Project progsets may be
        - Standalone progsets
        - Contained in a Result

    This function is a generator that allows iteration over all progsets in a project

    :param proj: A Project object
    :return: A progset (via yield)

    Example usage:

    for progset in all_progsets(proj):
        do_stuff(progset)

    """
    from .results import Result

    for progset in proj.progsets.values():
        yield (progset)

    for result in proj.results.values():
        if isinstance(result, list):
            for r in result:
                if r.model.progset is not None:
                    yield r.model.progset
        elif isinstance(result, Result) and result.model.progset is not None:
            yield result.model.progset


def all_frameworks(proj):
    """Helper generator to iterate over all frameworks in a project

    Project frameworks may be
        - Standalone frameworks
        - Contained in a Result

    This function is a generator that allows iteration over all frameworks in a project

    :param proj: A Project object
    :return: A framework (via yield)

    """
    from .results import Result

    if proj.framework:
        yield proj.framework

    for result in proj.results.values():
        if isinstance(result, list):
            for r in result:
                yield r.framework
        elif isinstance(result, Result):
            yield result.framework


@migration("Project", "1.0.5", "1.0.6", "Simplify ParameterSet storage")
def _simplify_parset_storage(proj):
    # ParameterSets in 1.0.5 store the parameters keyed by the type e.g. 'cascade','comp'
    # In 1.0.6 they are flat
    for parset in proj.parsets.values():
        new_pars = sc.odict()
        for par_type, par_list in parset.pars.items():
            for par in par_list:
                new_pars[par.name] = par
        parset.pars = new_pars
        del parset.par_ids
    return proj


@migration("Project", "1.0.7", "1.0.8", "Add version information to model")
def _add_model_version(proj):
    # Note that this is a legacy update via the Project and therefore Results that
    # are stored separately will not receive this migration. It is unlikely that any
    # Results have been stored in this form though.
    def add_version(res, p):
        res.model.version = p.version
        res.model.gitinfo = p.gitinfo
        res.model.created = p.created

    for result in all_results(proj):
        add_version(result, proj)

    return proj


@migration("ProgramSet", "1.0.8", "1.0.9", "Add currency and units to progset quantities")
def _add_currency_and_units(progset):

    # If the progset was saved prior to 1.23, it would have no version but it might have already
    # had these migrations applied. Therefore we need to check if they have already been run
    if hasattr(progset, "currency"):
        return progset

    progset.currency = "$"
    for program in progset.programs.values():
        program.baseline_spend.units = progset.currency + "/year"
        program.spend_data.units = progset.currency + "/year"
        program.unit_cost.units = progset.currency + "/person"
        program.capacity.units = "people/year"
        program.saturation.units = FS.DEFAULT_SYMBOL_INAPPLICABLE
        program.coverage.units = "people/year"

    return progset


@migration("ProgramSet", "1.0.9", "1.0.10", "Remove target_pars from Programs")
def _remove_target_pars(progset):

    for program in progset.programs.values():
        if hasattr(program, "target_pars"):
            del program.target_pars

    return progset


@migration("Project", "1.0.10", "1.0.11", "Add result update flag to Project")
def _add_result_update_flag(proj):
    proj._update_required = False
    return proj


@migration("Project", "1.0.12", "1.0.13", "Add timescale to parameters")
def _add_timescale(proj):
    for _, spec in proj.framework.pars.iterrows():
        if proj.framework.transitions[spec.name]:
            proj.framework.pars.at[spec.name, "timescale"] = 1.0  # Default timescale - note that currently only transition parameters are allowed to have a timescale that is not None

            if not spec["format"]:
                if not proj.data:
                    raise Exception('The Framework now needs to define the units for transition parameters, but the current one does not define units for Parameter "%s" and data was not saved either, so cannot infer the unit type. Please modify the Framework spreadsheet to add units' % (spec.name))
                else:
                    # Get the units from the first ts associated with the table
                    units = set([x.units.lower().strip() for x in proj.data.tdve[spec.name].ts.values()])
                    if len(units) == 1:
                        proj.framework.pars.at[spec.name, "format"] = list(units)[0]
                    else:
                        raise Exception('Parameters must now have a single unit for all populations. However, the existing data has more than one unit type associated with Parameter "%s" so it is no longer valid.' % (spec.name))

    return proj


@migration("Project", "1.0.13", "1.0.14", "Parameters use TimeSeries internally")
def _parameter_use_timeseries(proj):
    for parset in proj.parsets.values():
        for par in parset.all_pars():

            par.ts = dict()
            for pop in par.t.keys():
                par.ts[pop] = atomica.TimeSeries(units=par.y_format[pop])
                if par.t[pop] is None:
                    continue
                elif len(par.t[pop]) == 1 and not np.isfinite(par.t[pop][0]):
                    # It was an assumption
                    par.ts[pop].assumption = par.y[pop][0]
                else:
                    par.ts[pop].t = par.t[pop].tolist()
                    par.ts[pop].vals = par.y[pop].tolist()

            del par.y_format
            del par.t
            del par.y
            del par.autocalibrate

    return proj


@migration("Project", "1.0.14", "1.0.15", "Internal model tidying")
def _model_tidying(proj):
    for result in all_results(proj):
        for pop in result.model.pops:
            for charac in pop.characs:
                charac._vals = charac.internal_vals
                charac._is_dynamic = charac.dependency
                del charac.internal_vals
                del charac.dependency
            for par in pop.pars:
                par._is_dynamic = par.dependency
                par._precompute = False
                del par.dependency
    return proj


def _convert_atomica_spreadsheet(placeholder):
    new = sc.Spreadsheet(source=io.BytesIO(placeholder.data), filename=placeholder.filename)
    new.created = placeholder.load_date
    new.modified = placeholder.load_date
    return new


@migration("Project", "1.0.15", "1.0.16", "Replace AtomicaSpreadsheet in project")
def _convert_project_spreadsheets(proj):
    if proj.databook is not None:
        proj.databook = _convert_atomica_spreadsheet(proj.databook)
    if proj.progbook is not None:
        proj.progbook = _convert_atomica_spreadsheet(proj.progbook)
    return proj


@migration("ProjectFramework", "1.0.15", "1.0.16", "Replace AtomicaSpreadsheet in framework")
def _convert_framework_spreadsheets(framework):
    if framework.spreadsheet is not None:
        framework.spreadsheet = _convert_atomica_spreadsheet(framework.spreadsheet)
    return framework


@migration("ProgramSet", "1.0.16", "1.0.17", "Rename capacity constraint")
def _rename_capacity_constraint(progset):
    for prog in progset.programs.values():
        if hasattr(prog, "capacity"):
            prog.capacity_constraint = prog.capacity
            del prog.capacity
    return progset


@migration("Result", "1.0.27", "1.0.28", "Rename link labels")
def _rename_link_labels(result):
    for pop in result.model.pops:
        for link in pop.links:
            link.id = link.id[0:3] + (link.parameter.name + ":flow",)
    result.model._set_vars_by_pop()
    return result


@migration("Project", "1.0.30", "1.1.3", "Replace scenarios")
def _replace_scenarios(proj):
    # This migration upgrades existing scenarios to match the latest definitions
    from .scenarios import ParameterScenario, BudgetScenario, CoverageScenario
    from .utils import NDict, TimeSeries

    new_scens = NDict()

    for name, scen in proj.scens.items():

        scen_name = scen.name
        active = scen.active

        try:
            parsetname = proj.parset(scen.parsetname).name
        except Exception:
            parsetname = proj.parsets[-1].name

        if isinstance(scen, ParameterScenario):
            new_scen = scen  # No need to migrate parameter scenarios

        elif isinstance(scen, BudgetScenario):
            # Convert budget scenario to instructions based on existing logic
            if scen.alloc_year is not None:
                # If the alloc_year is prior to the program start year, then just use the spending value directly for all times
                # For more sophisticated behaviour, the alloc should be passed into the BudgetScenario as a TimeSeries
                alloc = sc.odict()
                for prog_name, val in scen.alloc.items():
                    assert not isinstance(val, TimeSeries)  # Value must not be a TimeSeries
                    if val is None:
                        continue  # Use default spending for any program that does not have a spending overwrite
                    alloc[prog_name] = TimeSeries(scen.alloc_year, val)
                    if scen.alloc_year > scen.start_year and proj.progsets:
                        # Add in current spending if a programs instance already exists
                        progset = proj.progsets[-1]
                        # If adding spending in a future year, linearly ramp from the start year
                        spend_data = progset.programs[prog_name].spend_data
                        alloc[prog_name].insert(scen.start_year, spend_data.interpolate(scen.start_year))  # This will result in a linear ramp
            else:
                alloc = sc.odict()
                for prog_name, val in scen.alloc.items():
                    if not isinstance(val, TimeSeries):
                        alloc[prog_name] = TimeSeries(scen.start_year, val)
                    else:
                        alloc[prog_name] = sc.dcp(val)
            for ts in alloc.values():
                ts.vals = [x * scen.budget_factor for x in ts.vals]

            try:
                progsetname = proj.progset(scen.progsetname).name
            except Exception:
                progsetname = proj.parsets[-1].name

            new_scen = atomica.BudgetScenario(name=scen_name, active=active, parsetname=parsetname, progsetname=progsetname, alloc=alloc, start_year=scen.start_year)

        elif isinstance(scen, CoverageScenario):
            coverage = sc.odict()
            for prog_name, val in scen.coverage.items():
                if not isinstance(val, TimeSeries):
                    coverage[prog_name] = TimeSeries(scen.start_year, val)
                else:
                    coverage[prog_name] = sc.dcp(val)

            try:
                progsetname = proj.progset(scen.progsetname).name
            except Exception:
                progsetname = proj.parsets[-1].name

            new_scen = atomica.CoverageScenario(name=scen_name, active=active, parsetname=parsetname, progsetname=progsetname, coverage=coverage, start_year=scen.start_year)

        new_scens.append(new_scen)

    proj.scens = new_scens
    return proj


@migration("ProgramSet", "1.2.0", "1.3.0", "Add population type")
def _add_pop_type_progset(progset):
    for pop in progset.pops.keys():
        if sc.isstring(progset.pops[pop]):
            progset.pops[pop] = {"label": progset.pops[pop], "type": FS.DEFAULT_POP_TYPE}

    for comp in progset.comps.keys():
        if sc.isstring(progset.comps[comp]):
            progset.comps[comp] = {"label": progset.comps[comp], "type": FS.DEFAULT_POP_TYPE}

    for par in progset.pars.keys():
        if sc.isstring(progset.pars[par]):
            progset.pars[par] = {"label": progset.pars[par], "type": FS.DEFAULT_POP_TYPE}

    return progset


@migration("Project", "1.2.0", "1.3.0", "Add population type")
def _add_pop_type(proj):

    for fw in all_frameworks(proj):

        # Add default population type sheet
        fw.sheets["population types"] = [pd.DataFrame.from_records([(FS.DEFAULT_POP_TYPE, "Default")], columns=["code name", "description"])]
        fw.comps["population type"] = FS.DEFAULT_POP_TYPE
        fw.characs["population type"] = FS.DEFAULT_POP_TYPE
        fw.pars["population type"] = FS.DEFAULT_POP_TYPE
        fw.interactions["to population type"] = FS.DEFAULT_POP_TYPE
        fw.interactions["from population type"] = FS.DEFAULT_POP_TYPE

    if proj.data:
        for pop_spec in proj.data.pops.values():
            pop_spec["type"] = FS.DEFAULT_POP_TYPE

        # Fix up TDVE types
        # Fix up transfers and interactions
        for tdve in proj.data.tdve.values():
            tdve.type = FS.DEFAULT_POP_TYPE

        for interaction in proj.data.transfers + proj.data.interpops:
            interaction.from_pop_type = FS.DEFAULT_POP_TYPE
            interaction.to_pop_type = FS.DEFAULT_POP_TYPE

    for parset in proj.parsets.values():
        parset.pop_types = [pop["type"] for pop in proj.data.pops.values()]  # If there are parsets without data, then we don't know what pop types to add. Project is essentially incomplete and considered unusable

    for result in all_results(proj):
        for pop in result.model.pops:
            pop.type = FS.DEFAULT_POP_TYPE

    return proj


@migration("Project", "1.3.0", "1.4.0", "Parameter can be derivative")
def _add_project_derivatives(proj):
    for fw in all_frameworks(proj):
        fw.pars["is derivative"] = "n"
    return proj


@migration("Result", "1.3.0", "1.4.0", "Parameter can be derivative")
def _add_result_derivatives(result):
    for pop in result.model.pops:
        for par in pop.pars:
            par.derivative = False
    return result


@migration("Project", "1.4.3", "1.5.0", "Parameters with functions can be overwritten")
def _add_parset_disable_function(proj):
    # Add skip_function flag to parset Parameter instances
    for parset in proj.parsets.values():
        for par in parset.all_pars():
            par.skip_function = sc.odict.fromkeys(par.ts, None)
    return proj


@migration("Result", "1.4.3", "1.5.0", "Parameters with functions can be overwritten")
def _result_add_skip_flag(result):
    for pop in result.model.pops:
        for par in pop.pars:
            par.skip_function = None
    return result


@migration("Project", "1.5.1", "1.5.2", "OptimInstruction has separate adjustment and start years")
def _separate_optiminstruction_years(proj):
    if hasattr(proj, "optims"):
        for optim in proj.optims.values():
            if "adjustment_year" not in optim.json:
                optim.json["adjustment_year"] = optim.json["start_year"]
    return proj


@migration("Project", "1.7.0", "1.8.0", "Parameters store interpolation method, deprecate scenario smooth onset")
def _add_parameter_interpolation_method(proj):
    for parset in proj.parsets.values():
        for par in parset.all_pars():
            par._interpolation_method = "pchip"  # New projects will default to linear, but migrations use pchip to ensure results don't change
    for scen in proj.scens.values():
        if isinstance(scen, atomica.ParameterScenario):
            for par_name in scen.scenario_values.keys():
                for pop_name in scen.scenario_values[par_name].keys():
                    if "smooth_onset" in scen.scenario_values[par_name][pop_name]:
                        logger.warning("Parameter scenario smooth onset is deprecated and will not be used")
    return proj


@migration("Project", "1.8.0", "1.9.0", "OptimInstructions functionality moved to apps")
def _refactor_optiminstructions(proj):
    if hasattr(proj, "optims"):
        delkeys = []
        for k, v in proj.optims.items():
            if isinstance(v, _Placeholder) and hasattr(v, "json"):  # If it was previously an OptimInstructions
                # This was a project from the FE, which stores the optimization JSON dicts in
                if not hasattr(proj, "optim_jsons"):
                    proj.optim_jsons = []

                json = v.json
                for prog_name in json["prog_spending"].keys():
                    spend = json["prog_spending"][prog_name]
                    try:
                        prog_label = proj.progsets[-1].programs[prog_name].label
                    except Exception:
                        prog_label = prog_name
                    json["prog_spending"][prog_name] = {"min": spend[0], "max": spend[1], "label": prog_label}
                proj.optim_jsons.append(json)
                delkeys.append(k)
        for k in delkeys:
            del proj.optims[k]
    else:
        proj.optims = atomica.NDict()  # Make sure it's defined, even if it's empty

    return proj


@migration("Project", "1.10.0", "1.11.0", "TDVE stores headings to write internally")
def _add_internal_flags_to_tdve(proj):
    # This migration adds missing attributes to TDVE and TDC objects
    if proj.data:
        for tdve in proj.data.tdve.values():
            tdve.assumption_heading = "Constant"
            tdve.write_assumption = True
            tdve.write_units = True
            tdve.write_uncertainty = True
            tdve.comment = None

        for tdc in proj.data.transfers + proj.data.interpops:
            tdc.assumption_heading = "Constant"
            tdc.write_assumption = True
            tdc.write_units = True
            tdc.write_uncertainty = True
            if not hasattr(tdc, "from_pops"):  # This was missed in the previous migration `add_pop_type` so add it in here
                # If the pop type is missing, then we must be using a legacy framework with only one pop type
                tdc.from_pop_type = list(proj.framework.pop_types.keys())[0]
                tdc.from_pops = list(proj.data.pops.keys())
                tdc.to_pop_type = list(proj.framework.pop_types.keys())[0]
                tdc.to_pops = list(proj.data.pops.keys())

    return proj


@migration("ProjectFramework", "1.12.2", "1.13.0", "Timed compartment updates to framework")
def _add_framework_timed_comps(fw):
    fw.pars["timed"] = "n"
    fw.comps["duration group"] = None
    return fw


@migration("Result", "1.12.2", "1.13.0", "Timed compartment updates to result")
def _add_result_timed_attribute(result):
    result.model.unlink()
    for pop in result.model.pops:
        for i, comp in enumerate(pop.comps):
            if comp.tag_birth:
                comp.__class__ = atomica.SourceCompartment
            elif comp.tag_dead:
                comp.__class__ = atomica.SinkCompartment
            elif comp.is_junction:
                comp.__class__ = atomica.JunctionCompartment
                comp.duration_group = None
            del comp.tag_birth
            del comp.tag_dead
            del comp.is_junction
    result.model.relink()  # Make sure all of the references are updated to the new compartment instance - it has the same ID so it should be fine
    return result


@migration("Project", "1.14.0", "1.15.0", "Refactor migration update flag")
def _rename_update_field(proj):
    if not hasattr(proj, "_result_update_required"):
        proj._result_update_required = False
    proj._update_required = proj._result_update_required
    del proj._result_update_required

    for result in all_results(proj):
        result._update_required = False
    return proj


@migration("Project", "1.15.0", "1.16.0", "Projects may change due to uncapped probabilities")
def _proj_refactor_settings_storage(proj):
    proj._update_required = True
    return proj


@migration("Result", "1.15.0", "1.16.0", "Results may change due to uncapped probabilities")
def _result_refactor_settings_storage(result):
    result._update_required = True
    return result


@migration("Project", "1.16.0", "1.17.0", "Add sim end year validation to project settings")
def _add_end_year_to_project_settings(proj):
    proj.settings = atomica.ProjectSettings(**proj.settings.__dict__)
    return proj


@migration("Project", "1.17.0", "1.18.0", "Add data TDC and TDVE attributes")
def _add_tdc_tdve_attributes(proj):
    if proj.data:
        for tdve in proj.data.tdve.values():
            tdve.ts_attributes = {}
        for tdc in proj.data.transfers + proj.data.interpops:
            tdc.attributes = {}
            tdc.ts_attributes = {}
    return proj


@migration("Project", "1.19.0", "1.20.0", "Framework.transitions is a defaultdict")
def _framework_transitions_defaultdict(proj):
    for fw in all_frameworks(proj):
        fw.transitions = defaultdict(list, fw.transitions)
    return proj


@migration("ProgramSet", "1.23.1", "1.23.2", "ProgramSet records all compartments including non-targetable ones")
def _add_progset_non_targetable_flag(progset):
    for code_name, comp in progset.comps.items():
        if not isinstance(comp, dict):
            progset.comps[code_name] = {"label": comp, "type": None}
            comp = progset.comps[code_name]
        if "non_targetable" not in comp:
            comp["non_targetable"] = False
    return progset


@migration("ProjectFramework", "1.23.4", "1.24.0", "Change framework columns to numeric types")
def _convert_framework_columns(framework):
    # This migration can be performed by simple revalidation. It will also allow
    # any other validation-related changes to be updated
    for df in framework.sheets["transitions"]:
        if not pd.isna(df.index.name):
            df.reset_index(inplace=True)

    framework._validate()
    return framework
