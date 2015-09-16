from invenio.modules.circulation.api.utils import ValidationExceptions
from invenio.modules.circulation.api.loan_cycle import cancel_clcs
from invenio.modules.circulation.models import CirculationLoanCycle


def _check_status(statuses, objs):
    if not all(map(lambda x: x.current_status in statuses, objs)):
        raise Exception('The object is in the wrong state.')


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
        item.current_state = 'on_shelf'
        item.save()
