PACKAGE_NAME = 'tracy'
DB_NAME = 'tracy'
API_PORT = 9004

# Logging
LOG_FILE = '/home/user/log/tracy.log'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_SIZE = 100000   # bytes
LOG_COUNT = 100


# Import local settings
try:
    from local_settings import *
except ImportError:
    pass
