from datetime import datetime, timedelta
import logging

from systools.system import loop, timer

from tracy import Log, AggregatedLog


logger = logging.getLogger(__name__)


def aggregate_logs():
    Log.remove({'created': {'$lt': datetime.utcnow() - timedelta(days=90)}},
            safe=True)

    key = ['name', 'msg']
    specs = {}
    initial = {
        'count': 0,
        'begin': 0,
        'end': 0,
        'exception': False,
        'msgs': [],
        }
    reduce_ = """function ( current, result ) {
    result.count++;

    if (result.begin == 0 || current.created < result.begin) {
        result.begin = current.created;
    }
    if (result.end == 0 || current.created < result.end) {
        result.end = current.created;
    }
    if (current.ext_text) {
        result.exception = true;
    }
    var messagesLength = result.msgs.length;
    if (messagesLength < 10) {
        var message = current.exc_text || current.message;
        var hasMsg = false;
        for (var i = 0; i < messagesLength; i++) {
            if (result.msgs[i][0].message == message) {
                result.msgs[i][1]++;
                hasMsg = true;
                break;
            }
        }
        if (!hasMsg) {
            result.msgs.push([{
                'message': message,
                'funcName': current.funcName,
                'lineno': current.lineno,
                'pathname': current.pathname,
                }, 1]);
        }
    }
}
"""
    finalize = None
    docs = Log().col.group(key, specs, initial,
            reduce_, finalize)
    AggregatedLog.drop()
    AggregatedLog.insert(docs, safe=True)

@loop(minutes=60)
@timer()
def run():
    aggregate_logs()
