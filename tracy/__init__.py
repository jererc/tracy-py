from datetime import datetime
import logging

from factory import Factory

from tracy import settings
from tracy.utils.db import Model, connect


DEFAULT_SETTINGS = {
    'tests_files': [],
    'tests_delta': 8,     # hours
    'logs_paths': [],
    'logs_line_pattern': r'^\d\d\d\d-\d\d-\d\d\b',
    }

logger = logging.getLogger(__name__)
connect(settings.DB_NAME)


class DbHandler(logging.Handler):

    def _format_record(self, record):
        record.message = record.msg % record.args if record.args else record.msg
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None

        res = {}
        for key in ('created', 'exc_text', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'message', 'module',
                'msg', 'name', 'pathname', 'process', 'args'):
            res[key] = getattr(record, key, None)
        res['created'] = datetime.utcfromtimestamp(res['created'])
        return res

    def emit(self, record):
        try:
            record = self._format_record(record)
            Log.insert(record, safe=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class Log(Model):
    COL = 'logs'


class AggregatedLog(Model):
    COL = 'logs.aggregated'


class Test(Model):
    COL = 'tests'


class TestInfo(Model):
    COL = 'tests.info'


class Settings(Model):
    COL = 'settings'

    @classmethod
    def get_settings(cls, section, key=None, default=None):
        res = cls.find_one({'section': section}) or {}
        settings = res.get('settings', DEFAULT_SETTINGS.get(section, {}))
        return settings.get(key, default) if key else settings

    @classmethod
    def set_setting(cls, section, key, value):
        cls.update({'section': section},
                {'$set': {'section': section, 'settings.%s' % key: value}},
                upsert=True)

    @classmethod
    def set_settings(cls, section, settings, overwrite=False):
        doc = {
            'section': section,
            'settings': settings,
            }
        cls.update({'section': section},
                doc if overwrite else {'$set': doc}, upsert=True)


def get_factory():
    return Factory(collection=settings.PACKAGE_NAME)
