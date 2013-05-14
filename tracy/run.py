#!/usr/bin/env python
import logging
from logging.handlers import RotatingFileHandler

from systools.system import get_package_modules

from tracy import settings, DbHandler, get_factory


WORKERS_DIR = 'workers'

logging.basicConfig(level=logging.DEBUG)


def main():
    factory = get_factory()
    factory.remove(daemon=True)

    # Logging handlers
    fh = RotatingFileHandler(settings.LOG_FILE, 'a',
            settings.LOG_SIZE, settings.LOG_COUNT)
    fh.setFormatter(logging.Formatter(settings.LOG_FORMAT))
    dh = DbHandler(logging.ERROR)
    factory.logging_handlers = (fh, dh)

    for module in get_package_modules(WORKERS_DIR):
        if module != '__init__':
            target = '%s.%s.%s.run' % (settings.PACKAGE_NAME, WORKERS_DIR, module)
            factory.add(target=target, daemon=True)

    factory.run()


if __name__ == '__main__':
    main()
