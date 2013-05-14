import os.path
from glob import glob
import re
import logging

from flask import request, jsonify

from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING

from systools.system.webapp import crossdomain, serialize

from tracy import AggregatedLog, Log, Test, TestInfo, Settings
from tracy.apps import app
from tracy.utils.utils import parse_log


logger = logging.getLogger(__name__)


@app.route('/status', methods=['GET'])
@crossdomain(origin='*')
def check_status():
    return jsonify(result='tracy')

@app.route('/error/list', methods=['GET'])
@crossdomain(origin='*')
def list_errors():
    items = [d for d in AggregatedLog.find(sort=[('end', DESCENDING)])]
    return serialize({'result': items})

@app.route('/error/remove', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def remove_errors():
    data = request.json
    if not data.get('id'):
        return jsonify(error='missing id')

    id = ObjectId(data['id'])
    res = AggregatedLog.find_one({'_id': id})
    if res:
        msgs = [m[0] for m in res['msgs']]
        Log.remove({'$or': [
                {'msg': {'$in': msgs}},
                {'exc_text': {'$in': msgs}},
                ]})
        AggregatedLog.remove({'_id': id})

    return jsonify(result=True)

@app.route('/test/list', methods=['GET'])
@crossdomain(origin='*')
def list_tests():
    items = [d for d in Test.find(sort=[('created', ASCENDING)])]
    return serialize({'result': items})

@app.route('/test/info', methods=['GET'])
@crossdomain(origin='*')
def get_tests_info():
    info = TestInfo.find_one() or {}
    return serialize({'result': info})

@app.route('/test/reset', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def reset_tests():
    TestInfo.drop()
    return jsonify(result=True)

@app.route('/log/list', methods=['GET'])
@crossdomain(origin='*')
def list_logs():
    items = []
    logs_paths = Settings.get_settings('logs_paths') or []
    for path in logs_paths:
        for res in sorted(glob('%s/*.log' % path)):
            items.append({
                    'file': res,
                    'name': os.path.splitext(os.path.basename(res))[0],
                    })

    return serialize({'result': items})

@app.route('/log/get', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def get_log():
    file = request.json.get('file')
    if not file:
        return jsonify(error='missing file')

    logs_line_pattern = Settings.get_settings('logs_line_pattern') or ''
    re_log_line = re.compile(logs_line_pattern, re.I)
    try:
        lines = parse_log(file, 1000, re_head=re_log_line)
        res = '\n'.join(lines).decode('utf-8')
    except Exception, e:
        return jsonify(error='failed to get log: %s' % str(e))
    return jsonify(result=res)

@app.route('/settings/list', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def list_settings():
    settings = {}
    for section in ('tests_files', 'tests_delta', 'logs_paths',
            'logs_line_pattern'):
        settings[section] = Settings.get_settings(section)
    return serialize({'result': settings})

@app.route('/settings/update', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def update_settings():
    data = request.json
    for section, settings in data.items():
        Settings.set_settings(section, settings, overwrite=True)
    return jsonify(result=True)
