# Central file for migrating Projects
from distutils.version import LooseVersion
from .system import logger, AtomicaException
from .version import version
import sciris as sc
from .results import Result
from .structure import FrameworkSettings as FS

available_migrations = [] # This list stores all of the migrations that are possible

class Migration:
    # This class stores a migration function together with all required metadata. It would
    # normally be instantiated using the `migration` decorator below
    def __init__(self, original_version, new_version, description, fcn, date=None):
        self.original_version = original_version
        self.new_version = new_version
        self.description = description
        self.date = date
        self.fcn = fcn

    def upgrade(self, proj):
        logger.debug('MIGRATION: Upgrading %s -> %s (%s)' % (self.original_version,self.new_version,self.description))
        proj = self.fcn(proj) # Run the migration function
        proj.version = self.new_version # Update the version
        return proj

    def __repr__(self):
        return 'Migration(%s->%s)' % (self.original_version,self.new_version)


def migration(original_version, new_version, description, date=None):
    # This decorator is used to register a migration function.
    # The decorator takes in the metadata such as the old and new version strings
    def register(f):
        available_migrations.append(Migration(original_version, new_version, description, fcn=f, date=date))
        return f
    return register

def migrate(proj):
    # Run all of the migrations in the list of available migrations. The migrations are run in ascending order, as long
    # as the version is <= the migration's original version. This way, migrations don't need to be added if a version number
    # change takes place without actually needing a migration - instead, when adding a migration, just use whatever version
    # numbers are appropriate at the time the change is introduced, it will behave sensibly
    migrations = sorted(available_migrations, key=lambda m: LooseVersion(m.original_version))
    logger.info('Migrating Project "%s" from %s->%s' % (proj.name, proj.version, migrations[-1].new_version))
    for m in migrations: # Run the migrations in increasing version order
        if proj.version > m.original_version:
            continue
        else:
            proj = m.upgrade(proj)
    proj.version = version # Set project version to the current Atomica version
    return proj

@migration('1.0.5', '1.0.6','Simplify ParameterSet storage')
def simplify_parset_storage(proj):
    # ParameterSets in 1.0.5 store the parameters keyed by the type e.g. 'cascade','comp'
    # In 1.0.6 they are flat
    for parset in proj.parsets.values():
        new_pars = sc.odict()
        for par_type,par_list in parset.pars.items():
            for par in par_list:
                new_pars[par.name] = par
        parset.pars = new_pars
        del parset.par_ids
    return proj

@migration('1.0.7', '1.0.8','Add version information to model/results')
def add_model_version(proj):

    def add_version(res,p):
        res.model.version = p.version
        res.model.gitinfo = p.gitinfo
        res.model.created = p.created

    for result in proj.results.values():
        if isinstance(result,list):
            for r in result:
                add_version(r,proj)
        elif isinstance(result,Result):
            add_version(result,proj)

    return proj

@migration('1.0.8', '1.0.9','Add currency and units to progset quantities')
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

    for progset in proj.progsets.values():
        add_units(progset)

    for result in proj.results.values():
        if result.model.progset is not None:
            add_units(result.model.progset)

    return proj

@migration('1.0.9', '1.0.10','Remove target_pars from Programs')
def remove_target_pars(proj):

    def remove_pars(progset):
        for program in progset.programs.values():
            del program.target_pars

    for progset in proj.progsets.values():
        remove_pars(progset)

    for result in proj.results.values():
        if result.model.progset is not None:
            remove_pars(result.model.progset)
