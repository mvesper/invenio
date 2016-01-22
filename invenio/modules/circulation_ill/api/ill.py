from invenio.modules.circulation.api.circulation import loan_items
from invenio.modules.circulation.api.item import create as create_item
from invenio.modules.circulation.api.item import lose_items
from invenio.modules.circulation.api.event import create as create_event
from invenio.modules.circulation.api.utils import email_notification
from invenio.modules.circulation.api.utils import ValidationExceptions
from invenio.modules.circulation.api.loan_cycle import loan_extension

from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle)
from invenio.modules.circulation_ill.models import IllLoanCycle


def _create_ill_temporary_item(record):
    ill_tmp = 'ill_temporary_no_value'
    status = CirculationItem.STATUS_ON_SHELF
    group = CirculationItem.GROUP_BOOK
    item = create_item(record.id, 1, ill_tmp, ill_tmp, ill_tmp, ill_tmp,
                       ill_tmp, ill_tmp, status, group)
    item.additional_statuses.append('ill_temporary')
    item.save()

    return item


def request_ill(user, record, start_date, end_date,
                delivery=None, comments=''):
    delivery = IllLoanCycle.DELIVERY_DEFAULT if delivery is None else delivery

    item = _create_ill_temporary_item(record)

    ill_clc = IllLoanCycle.new(current_status=IllLoanCycle.STATUS_REQUESTED,
                               item=item, user=user,
                               start_date=start_date, end_date=end_date,
                               delivery=delivery, comments=comments)

    create_event(user_id=user.id, item_id=item.id,
                 ill_loan_cycle_id=ill_clc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_REQUEST)

    email_notification('ill_request', 'john.doe@cern.ch', user.email,
                       name=user.name, action='requested', items=item)

    return ill_clc


def try_confirm_ill_request(ill_loan_cycle):
    exceptions = []
    try:
        assert ill_loan_cycle.current_status == IllLoanCycle.STATUS_REQUESTED,\
                'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def confirm_ill_request(ill_loan_cycle):
    try:
        try_confirm_ill_request(ill_loan_cycle)
    except ValidationExceptions as e:
        raise e

    ill_loan_cycle.current_status = IllLoanCycle.STATUS_ORDERED
    ill_loan_cycle.save()

    create_event(ill_loan_cycle_id=ill_loan_cycle.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_ORDERED)

    email_notification('ill_ordered', 'john.doe@cern.ch',
                       ill_loan_cycle.user.email,
                       ill_loan_cycle=ill_loan_cycle)


def try_cancel_ill_request(ill_lc):
    exceptions = []
    try:
        assert (ill_lc.current_status == IllLoanCycle.STATUS_REQUESTED or
                ill_lc.current_status == IllLoanCycle.STATUS_ORDERED), \
                'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def cancel_ill_request(ill_lc):
    try:
        try_cancel_ill_request(ill_lc)
    except ValidationExceptions as e:
        raise e

    ill_lc.current_status = IllLoanCycle.STATUS_CANCELED
    ill_lc.save()

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_CANCELED)


def try_decline_ill_request(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_REQUESTED, \
                'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def decline_ill_request(ill_lc):
    try:
        try_decline_ill_request(ill_loan_cycle)
    except ValidationExceptions as e:
        raise e

    ill_loan_cycle.current_status = IllLoanCycle.STATUS_DECLINED
    ill_loan_cycle.save()

    create_event(ill_loan_cycle_id=ill_loan_cycle.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_DECLINED)

    email_notification('ill_declined', 'john.doe@cern.ch',
                       ill_loan_cycle.user.email,
                       ill_loan_cycle=ill_loan_cycle)


def try_deliver_ill(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_ORDERED, \
                'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def deliver_ill(ill_lc):
    try:
        try_deliver_ill(ill_lc)
    except ValidationExceptions as e:
        raise e

    import invenio.modules.circulation.models as models

    ill_lc.current_status = IllLoanCycle.STATUS_ON_LOAN
    ill_lc.save()

    ''' TODO: this is probably not needed
    ills = loan_items(ill_lc.user, [ill_lc.item],
                      ill_lc.start_date, ill_lc.end_date,
                      False, ill_lc.delivery)

    ill = ills[0]
    ill.additional_statuses.append('ill_loan_cycle')
    ill.save()
    '''
    ill_lc.item.current_status = models.CirculationItem.STATUS_ON_LOAN

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_DELIVERED)

    email_notification('ill_delivery', 'john.doe@cern.ch',
                       ill_lc.user.email,
                       ill_loan_cycle=ill_lc)


def try_request_ill_extension(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == CirculationLoanCycle.STATUS_ON_LOAN, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def request_ill_extension(ill_lc, requested_end_date):
    try:
        try_request_ill_extension(ill_lc)
    except ValidationExceptions as e:
        raise e

    ill_lc.desired_end_date = requested_end_date
    ill_lc.additional_statuses.append(IllLoanCycle.STATUS_EXTENSION_REQUESTED)
    ill_lc.save()

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_EXTENSION_REQUESTED)

    email_notification('ill_extension_request', 'john.doe@cern.ch',
                       ill_lc.user.email,
                       loan_cycle=ill_lc)

def try_confirm_ill_extension(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_ON_LOAN, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    try:
        s = IllLoanCycle.STATUS_EXTENSION_REQUESTED
        assert s in ill_lc.additional_statuses, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    try:
        assert ill_lc.desired_end_date is not None, \
                'A desired end date is necessary.'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def confirm_ill_extension(ill_lc):
    try:
        try_confirm_ill_extension(ill_lc)
    except ValidationExceptions as e:
        raise e

    ill_lc.end_date = ill_lc.desired_end_date
    ill_lc.desired_end_date = None
    ill_lc.additional_statuses.remove(IllLoanCycle.STATUS_EXTENSION_REQUESTED)
    ill_lc.save()

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_EXTENSION_CONFIRMED)

    email_notification('ill_extension_request_confirmed', 'john.doe@cern.ch',
                       ill_lc.user.email,
                       loan_cycle=ill_lc)


def try_decline_ill_extension(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_ON_LOAN, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    try:
        s = IllLoanCycle.STATUS_EXTENSION_REQUESTED
        assert s in ill_lc.additional_statuses, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    try:
        assert ill_lc.desired_end_date is not None, \
                'A desired end date is necessary.'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)

def decline_ill_extension(ill_lc):
    try:
        try_decline_ill_extension(ill_lc)
    except ValidationExceptions as e:
        raise e

    ill_lc.desired_end_date = None
    ill_lc.additional_statuses.remove(IllLoanCycle.STATUS_EXTENSION_REQUESTED)
    ill_lc.save()

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_EXTENSION_DECLINED)

    email_notification('ill_extension_request_declined', 'john.doe@cern.ch',
                       ill_lc.user.email,
                       loan_cycle=ill_lc)


def try_return_ill(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_ON_LOAN, \
                'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def return_ill(ill_loan_cycle):
    # This function should be called using a signal once the corresponding
    # item is returned
    try:
        try_return_ill(ill_loan_cycle)
    except ValidationExceptions as e:
        raise e

    ill_loan_cycle.current_status = IllLoanCycle.STATUS_FINISHED
    ill_loan_cycle.save()

    create_event(ill_loan_cycle_id=ill_loan_cycle.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_FINISHED)


def try_send_back_ill(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_FINISHED, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def send_back_ill(ill_loan_cycle):
    try:
        try_send_back_ill(ill_loan_cycle)
    except ValidationExceptions as e:
        raise e

    ill_loan_cycle.current_status = IllLoanCycle.STATUS_SEND_BACK
    ill_loan_cycle.save()

    create_event(ill_loan_cycle_id=ill_loan_cycle.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_SEND_BACK)


def try_lose_ill(ill_lc):
    exceptions = []
    try:
        assert ill_lc.current_status == IllLoanCycle.STATUS_ON_LOAN, \
               'The ill loan cycle is in the wrong state'
    except AssertionError as e:
        exceptions.append(('ill', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def lose_ill(ill_lc):
    try:
        try_lose_ill(ill_lc)
    except ValidationExceptions as e:
        raise e

    ill_lc.current_status = IllLoanCycle.STATUS_MISSING
    ill_lc.save()

    create_event(ill_loan_cycle_id=ill_lc.id,
                 event=IllLoanCycle.EVENT_ILL_CLC_LOST)

    lose_items([ill_lc.item])
