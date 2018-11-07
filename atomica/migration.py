"""
Manage Project versions and migration

Migration refers to updating old :py:class:`Project` instances so that they
can be run with more recent versions of Atomica. This module defines

- A set of 'migration functions' that each transform a :py:class:`Project` instance from one
  version to another
- An entry-point that sequentially calls the migration functions to update a project to
  the current version used in Atomica

"""

import sys
from distutils.version import LooseVersion
from .system import logger, AtomicaException
from .version import version
import sciris as sc
from .results import Result
from . import framework as FS
import atomica
import types

### MODULE MIGRATIONS
#
# In this section, make changes to the Atomica module structure to enable pickle files
# to be loaded at all

# First, add any placeholder modules that have been subsequently removed
atomica.structure = types.ModuleType('structure') # Removed 'structure' module in 1.0.12 20181107
sys.modules['atomica.structure'] = atomica.structure

# Then, remap any required classes
atomica.structure.TimeSeries = atomica.utils.TimeSeries # Moved 'TimeSeries' in 1.0.12 20181107

### PROJECT MIGRATIONS
#
# The remaining code manages upgrading Project objects and their contents after they
# have been unpickled and instantiated

# This list stores all of the migrations that are possible
available_migrations = []

class Migration:
    """ Class representation of a migration

    This class stores a migration function together with all required metadata. It would
    normally be instantiated using the `migration` decorator, which also registers the
    migration by adding it to the `available_migrations` list

    """

    def __init__(self, original_version, new_version, description, fcn, date=None, changes_results=False):
        self.original_version = original_version
        self.new_version = new_version
        self.description = description
        self.changes_results = changes_results
        self.date = date
        self.fcn = fcn

    def upgrade(self, proj):
        logger.debug('MIGRATION: Upgrading %s -> %s (%s)' % (self.original_version, self.new_version, self.description))
        proj = self.fcn(proj)  # Run the migration function
        if proj is None:
            raise AtomicaException('Migration "%s" returned None, it is likely missing a return statement' % (str(self)))
        proj.version = self.new_version  # Update the version
        if self.changes_results:
            proj._result_update_required = True
        return proj

    def __repr__(self):
        return 'Migration(%s->%s)' % (self.original_version, self.new_version)


def migration(original_version, new_version, description, date=None, changes_results=False):
    """ Decorator to register migration functions

    This decorator constructs a `Migration` object from a decorated migration function, and registers it
    in the module's list of migrations to be run when calling migrate()

    :param original_version: Version string for the start version. Function will only run on projects whose version is <= this
    :param new_version: The resulting project is assigned this version
    :param description: A brief overview of the purpose of this migration
    :param date: Optionally specify the date when this migration was written
    :param changes_results: Optionally flag that changes to model output may occur
    :return: None

    Example usage::

        @migration('1.0.0', '1.0.1', 'Upgrade project', changes_results=True)
        def update_project(proj):
            ...
            return proj

    The migration function (update_project()) takes a single argument which is a project object, and returns
    a project object. Decorating the function registers the migration and it will automatically be used by
    migrate() and therefore Project.load()

    """

    def register(f):
        available_migrations.append(Migration(original_version, new_version, description, fcn=f, date=date, changes_results=changes_results))
        return f
    return register


def migrate(proj):
    """ Update a project to the latest version

    Run all of the migrations in the list of available migrations. The migrations are run in ascending order, as long
    as the version is <= the migration's original version. This way, migrations don't need to be added if a version number
    change takes place without actually needing a migration - instead, when adding a migration, just use whatever version
    numbers are appropriate at the time the change is introduced, it will behave sensibly.

    Typically, this function would not be called manually - it happens automatically as part of `Project.load()`.

    Note that this function returns the updated Project object. Typically the migration functions will update a
    project in-place, but this syntax allows migrations to replace parts of the project (or the entire project)
    if that is ever necessary in the future. So do not rely on `migrate` having side-effects, make sure the
    returned Project object is retained. In principle we could dcp() the Project to ensure that only the
    copy gets migrated, but at this point it does not appear worth the performance overhead (since migration at the
    moment is only ever called automatically).

    :param proj: Project object to migrate
    :return: Updated Project object

    """

    migrations = sorted(available_migrations, key=lambda m: LooseVersion(m.original_version))
    if sc.compareversions(proj.version, version) >= 0:
        return proj
    else:
        logger.info('Migrating Project "%s" from %s->%s', proj.name, proj.version, version)
    for m in migrations:  # Run the migrations in increasing version order
        if sc.compareversions(proj.version, m.original_version) > 0:
            continue
        else:
            proj = m.upgrade(proj)

    proj.version = version  # Set project version to the current Atomica version
    if proj._result_update_required:
        logger.warning('Caution: due to migration, project results may be different if re-run.')
    return proj


def all_results(proj):
    """ Helper generator to iterate over all results in a project

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

    for result in proj.results.values():
        if isinstance(result, list):
            for r in result:
                yield r
        elif isinstance(result, Result):
            yield result


def all_progsets(proj):
    """ Helper generator to iterate over all progsets in a project

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

    for progset in proj.progsets.values():
        yield(progset)

    for result in proj.results.values():
        if isinstance(result, list):
            for r in result:
                if r.model.progset is not None:
                    yield r.model.progset
        elif isinstance(result, Result) and result.model.progset is not None:
            yield result.model.progset


@migration('1.0.5', '1.0.6', 'Simplify ParameterSet storage')
def simplify_parset_storage(proj):
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


@migration('1.0.7', '1.0.8', 'Add version information to model/results')
def add_model_version(proj):

    def add_version(res, p):
        res.model.version = p.version
        res.model.gitinfo = p.gitinfo
        res.model.created = p.created

    for result in all_results(proj):
        add_version(result, proj)

    return proj


@migration('1.0.8', '1.0.9', 'Add currency and units to progset quantities')
def add_model_version(proj):

    def add_units(progset):
        # Add in the default units
        progset.currency = '$'
        for program in progset.programs.values():
            program.baseline_spend.units = progset.currency + '/year'
            program.spend_data.units = progset.currency + '/year'
            program.unit_cost.units = progset.currency + '/person'
            program.capacity.units = 'people/year'
            program.saturation.units = FS.DEFAULT_SYMBOL_INAPPLICABLE
            program.coverage.units = 'people/year'

    for progset in all_progsets(proj):
        add_units(progset)

    return proj


@migration('1.0.9', '1.0.10', 'Remove target_pars from Programs')
def remove_target_pars(proj):

    def remove_pars(progset):
        for program in progset.programs.values():
            del program.target_pars

    for progset in all_progsets(proj):
        remove_pars(progset)

    return proj


@migration('1.0.10', '1.0.11', 'Add result update flag to Project')
def remove_target_pars(proj):
    proj._result_update_required = False
    return proj
