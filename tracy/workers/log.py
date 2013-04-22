from operator import itemgetter
import logging

from systools.system import loop, timer

from tracy import Log, AggregatedLog


logger = logging.getLogger(__name__)


def aggregate():
    AggregatedLog.drop()

    for res in Log.find():
        doc = {
            'name': res['name'],
            'funcName': res['funcName'],
            'lineno': res['lineno'],
            'pathname': res['pathname'],
            }
        if AggregatedLog.find_one(doc):
            continue

        to_update = {
            'begin': res['created'],
            'end': res['created'],
            'count': 0,
            }
        msgs = {}
        for res_ in Log.find(doc):
            to_update['count'] += 1
            if res_['created'] < to_update['begin']:
                to_update['begin'] = res_['created']
            elif res_['created'] > to_update['end']:
                to_update['end'] = res_['created']

            msg = res_['exc_text'] or res_['msg']
            if res_['exc_text']:
                to_update['exception'] = True
            msgs.setdefault(msg, 0)
            msgs[msg] += 1

        to_update['msgs'] = sorted(msgs.items(),
                key=itemgetter(1), reverse=True)

        for key, val in res.items():
            if key not in ('created', 'exc_text', 'msg'):
                doc[key] = val
        doc.update(to_update)

        AggregatedLog.insert(doc, safe=True)

@loop(minutes=5)
@timer()
def run():
    aggregate()
