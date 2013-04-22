import sys
import os.path
from datetime import datetime, timedelta
import inspect
import unittest
import logging

from systools.system import loop, timeout, timer

from tracy import Test, TestInfo, Settings


logger = logging.getLogger(__name__)


def get_tests_suite(file):
    path, filename = os.path.split(file)
    sys.path.insert(0, path)
    module_name = os.path.splitext(filename)[0]
    if module_name in sys.modules:
        del sys.modules[module_name]
    try:
        module = __import__(module_name, globals(), locals(), [], 0)
        return unittest.TestLoader().loadTestsFromModule(module)
    except ImportError, e:
        logger.error(str(e))

@timeout(hours=1)
def run_tests(file):
    suite = get_tests_suite(file)
    unittest.installHandler()
    logging.disable(logging.INFO)
    results = unittest.TextTestRunner(verbosity=2).run(suite)
    logging.disable(logging.NOTSET)
    unittest.removeHandler()
    return results

def get_info(data):
    obj, traceback = data
    cls = obj.__class__
    return {
        'name': str(obj),
        'file': inspect.getfile(cls).replace('.pyc', '.py'),
        'class': cls.__name__,
        'traceback': traceback,
        }

@loop(minutes=2)
@timer()
def run():
    delta = timedelta(hours=Settings.get_settings('tests_delta') or 12)
    if TestInfo.find_one({
            'finished': {'$gte': datetime.utcnow() - delta},
            }):
        return

    tests_info = {
        'started': datetime.utcnow(),
        'tests_run': 0,
        'errors': 0,
        'failures': 0,
        'skipped': 0,
        }
    files = Settings.get_settings('tests_files') or []
    for file in files:
        results = run_tests(file)
        ids = []
        for type in ('errors', 'failures', 'skipped'):
            for res in getattr(results, type):
                info = get_info(res)
                info['file'] = file
                info['type'] = type.rstrip('s')
                test = Test.find_one({
                        'name': info['name'],
                        'file': info['file'],
                        })
                if test:
                    test['tries'] = test.get('tries', 1) + 1
                else:
                    test = {
                        'created': datetime.utcnow(),
                        'tries': 1,
                        }
                test.update(info)
                id = Test.save(test, safe=True)
                ids.append(id)
                tests_info[type] += 1

        tests_info['tests_run'] += results.testsRun

        Test.remove({'file': file, '_id': {'$nin': ids}}, safe=True)

    tests_info['finished'] = datetime.utcnow()
    TestInfo.update({}, tests_info, upsert=True, safe=True)
