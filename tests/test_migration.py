from atomica.migration import migrate
from atomica.system import logger
logger.setLevel('DEBUG')

class MigrationTest():
    def __init__(self):
        self.name = 'asdf'
        self.version = '0.1'
        self.a = 1

x = MigrationTest()
x = migrate(x)
print(x.version)
print(x.a)
print(x.b)
