from invenio.modules.circulation.api.utils import ValidationExceptions
from invenio.modules.circulation.api.event import create as create_event
from invenio.modules.circulation.api.loan_cycle import (cancel_clcs,
                                                        overdue_clcs,
                                                        return_ill_clcs)
from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationEvent)
from invenio.modules.circulation.api.utils import update as _update

"""
This shall be utilized in the future
def try_functions(*funcs, **kwargs):
    exceptions = []
    for name, func in funcs:
        try:
            func(**kwargs)
        except Exception as e
            exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)
"""


def _check_status(statuses, objs):
    if not all(map(lambda x: x.current_status in statuses, objs)):
        raise Exception('The object is in the wrong state.')


def try_create(current_status):
    if current_status not in ['requested', 'ordered', 'claimed', 'in_process',
                              'on_shelf']:
        raise Exception('The Item is in the wrong status.')


def create(record_id, location_id, isbn, barcode, collection,
           description, current_status, item_group):
    try:
        try_create(current_status)
    except ValidationExceptions as e:
        raise e

    ci = CirculationItem.new(record_id=record_id,
                             location_id=location_id,
                             barcode=barcode, isbn=isbn, collection=collection,
                             current_status=current_status,
                             description=description,
                             item_group=item_group)

    description = 'Created in status: {0}'.format(current_status)
    create_event(item=ci, event=CirculationEvent.EVENT_ITEM_CREATE,
                 description=description)


def update(item, **kwargs):
    current_items, changed = _update(item, **kwargs)
    if changed:
        changes_str = ['{0}: {1} -> {2}'.format(key,
                                                current_items[key],
                                                changed[key])
                       for key in changed]
        create_event(item=item, event=CirculationEvent.EVENT_ITEM_CHANGE,
                     description=', '.join(changes_str))


def delete(item):
    create_event(item=item, event=CirculationEvent.EVENT_ITEM_DELETE)
    item.delete()


def try_lose_items(items):
    exceptions = []
    try:
        _check_status(['on_shelf', 'on_loan'], items)
    except Exception as e:
        exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def lose_items(items):
    try:
        try_lose_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        item.current_status = 'missing'
        item.save()
        create_event(item=item, event=CirculationEvent.EVENT_ITEM_MISSING)

        clcs = [x for status in ['on_loan', 'reserved', 'overdue']
                for x in CirculationLoanCycle.search(item=item,
                                                     current_status=status)]
        cancel_clcs(clcs)


def try_return_missing_items(items):
    exceptions = []
    try:
        _check_status(['missing'], items)
    except Exception as e:
        exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def return_missing_items(items):
    try:
        try_return_missing_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        item.current_status = 'on_shelf'
        item.save()
        create_event(item=item,
                     event=CirculationEvent.EVENT_ITEM_RETURNED_MISSING)


def try_process_items(items):
    exceptions = []
    try:
        _check_status(['requested', 'ordered', 'claimed', 'on_shelf'], items)
    except Exception as e:
        exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def process_items(items, description):
    try:
        try_process_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        item.current_status = 'in_process'
        item.save()
        create_event(item=item,
                     event=CirculationEvent.EVENT_ITEM_IN_PROCESS,
                     description=description)


def try_overdue_items(items):
    exceptions = []
    try:
        _check_status(['on_loan'], items)
    except Exception as e:
        exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def overdue_items(items):
    try:
        try_overdue_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        clcs = CirculationLoanCycle.search(item=item, current_status='on_loan')
        overdue_clcs(clcs)


def try_return_ill_items(items):
    exceptions = []
    try:
        _check_status(['on_loan'], items)
    except Exception as e:
        exceptions.append(('item', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def return_ill_items(items):
    try:
        try_return_ill_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        item.current_status = 'returned'
        item.saved()
        clcs = CirculationLoanCycle.search(item=item, current_status='on_loan')
        return_ill_clcs(clcs)


schema = {'lose_items': [],
          'return_missing_items': [],
          'process_items': [('description', 'string')],
          'overdue_items': []}
