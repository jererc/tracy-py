from operator import itemgetter
import logging

from systools.system import loop, timer

from tracy import Log, AggregatedLog


logger = logging.getLogger(__name__)


def aggregate_messages(messages):
    res = []
    for msg in messages:
        item = (msg, messages.count(msg))
        if item not in res:
            res.append(item)

    return sorted(res, key=itemgetter(1), reverse=True)

def aggregate_logs():
    AggregatedLog.drop()

    for res in Log.find():
        doc = {
            'name': res['name'],
            'msg': res['msg'],
            }
        if AggregatedLog.find_one(doc):
            continue

        to_update = {
            'begin': res['created'],
            'end': res['created'],
            'count': 0,
            }

        # Aggregate by message field
        msgs = []
        for log in Log.find(doc):
            to_update['count'] += 1
            if log['created'] < to_update['begin']:
                to_update['begin'] = log['created']
            elif log['created'] > to_update['end']:
                to_update['end'] = log['created']

            if log['exc_text']:
                to_update['exception'] = True

            msgs.append({
                    'message': log['exc_text'] or log['message'],
                    'funcName': log['funcName'],
                    'lineno': log['lineno'],
                    'pathname': log['pathname'],
                    })

        to_update['msgs'] = aggregate_messages(msgs)
        doc.update(to_update)

        AggregatedLog.insert(doc, safe=True)

@loop(minutes=5)
@timer()
def run():
    aggregate_logs()
