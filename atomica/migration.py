# Central file for migrating Projects
from distutils.version import LooseVersion
from .system import logger, AtomicaException

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

    def upgrade(self, obj):
        logger.debug('MIGRATION: Upgrading %s -> %s (%s)' % (self.original_version,self.new_version,self.description))
        obj = self.fcn(obj) # Run the migration function
        obj.version = self.new_version # Update the version
        return obj

    def __repr__(self):
        return 'Migration(%s->%s)' % (self.original_version,self.new_version)


def migration(original_version, new_version, description, date=None):
    # This decorator is used to register a migration function.
    # The decorator takes in the metadata such as the old and new version strings
    def register(f):
        available_migrations.append(Migration(original_version, new_version, description, fcn=f, date=date))
        return f
    return register

def migrate(obj):
    # Run all of the migrations in the list of available migrations. The migrations are run in ascending order, as long
    # as the version is <= the migration's original version. This way, migrations don't need to be added if a version number
    # change takes place without actually needing a migration - instead, when adding a migration, just use whatever version
    # numbers are appropriate at the time the change is introduced, it will behave sensibly
    migrations = sorted(available_migrations, key=lambda m: LooseVersion(m.original_version))
    logger.info('Migrating Project "%s" from %s->%s' % (obj.name, obj.version, migrations[-1].new_version))
    for m in migrations: # Run the migrations in increasing version order
        if obj.version > m.original_version:
            continue
        else:
            obj = m.upgrade(obj)
    return obj

# Examples: these will be removed once some real migrations are written
@migration('0.1', '0.2','Increment the version')
def increment_version(obj):
    obj.version = '0.2'
    return obj


@migration('0.2', '0.3','Change the number')
def change_number(obj):
    obj.a = 2
    return obj

@migration('0.4', '0.5','Change new field')
def change_number(obj):
    obj.b += 'bar'
    return obj

@migration('0.3', '0.4','Add new field')
def change_number(obj):
    obj.b = 'foo'
    return obj

