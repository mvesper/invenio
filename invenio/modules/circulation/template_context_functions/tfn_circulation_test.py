import datetime

from invenio.ext.template import render_template_to_string
from invenio.modules.circulation.models import CirculationItem


def has_items(record_id):
    return CirculationItem.search(record_id=record_id)


def encode_circulation_state(users, items, records, start_date, end_date):
    # :1::2015-09-22:2015-10-20:
    return '{items}:{users}:{records}:{start}:{end}:'.format(
            items=','.join(str(x) for x in items),
            users=','.join(str(x) for x in users),
            records=','.join(str(x) for x in records),
            start=start_date, end=end_date)


def template_context_function(record_id, user_id):
    if has_items(record_id):
        start = datetime.date.today()
        end = start + datetime.timedelta(weeks=4)
        link = encode_circulation_state([user_id], [], [record_id], start, end)
        return render_template_to_string('search/search_res_addition.html',
                                         state=link, record_id=record_id)
    return ''
