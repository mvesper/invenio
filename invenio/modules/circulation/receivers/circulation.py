from invenio.modules.circulation.signals import (circulation_search,
                                                 circulation_state,
                                                 circulation_actions)


def _circulation_search(sender, data):
    from invenio.modules.circulation.models import (CirculationUser,
                                                    CirculationItem,
                                                    CirculationRecord)

    search = data['search']
    return {'name': 'circulation',
            'result': (CirculationUser.search(search),
                       CirculationItem.search(search),
                       CirculationRecord.search(search))}


def _circulation_state(sender, data):
    import json
    from invenio.modules.circulation.models import (CirculationUser,
                                                    CirculationItem,
                                                    CirculationRecord)
    from invenio.modules.circulation.views.utils import (
            _get_cal_heatmap_dates,
            _get_cal_heatmap_range)

    def _enhance_record_data(records):
        q = 'record_id:{0}'
        for record in records:
            record.items = CirculationItem.search(q.format(record.id))
            for item in record.items:
                item.cal_data = json.dumps(_get_cal_heatmap_dates([item]))
                item.cal_range = _get_cal_heatmap_range([item])

    users = [CirculationUser.get(x) for x in data['user_ids']]
    items = [CirculationItem.get(x) for x in data['item_ids']]
    records = [CirculationRecord.get(x) for x in data['record_ids']]

    _enhance_record_data(records)

    return {'name': 'circulation',
            'result': (users, items, records)}


def _circulation_actions(sender, data):
    return {'name': 'circulation',
            'result': [('LOAN', 'loan'),
                       ('REQUEST', 'request'),
                       ('RETURN', 'return')]}


circulation_search.connect(_circulation_search, 'circulation_search')
circulation_state.connect(_circulation_state, 'circulation_state')
circulation_actions.connect(_circulation_actions, 'circulation_actions')
