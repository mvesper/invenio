from invenio.modules.circulation.models import (CirculationLoanRule,
                                                CirculationEvent)
from invenio.modules.circulation.api.event import create as create_event
from invenio.modules.circulation.api.utils import update as _update


def create(item_group, user_group, location_code, loan_period,
           extension_allowed):
    clr = CirculationLoanRule.new(item_group=item_group, user_group=user_group,
                                  location_code=location_code,
                                  loan_period=loan_period,
                                  extension_allowed=extension_allowed)

    create_event(loan_rule_id=clr.id, event=CirculationEvent.EVENT_LR_CREATE)

    return clr


def update(clr, **kwargs):
    current_items, changed = _update(clr, **kwargs)
    if changed:
        changes_str = ['{0}: {1} -> {2}'.format(key,
                                                current_items[key],
                                                changed[key])
                       for key in changed]
        create_event(loan_rule_id=clr.id,
                     event=CirculationEvent.EVENT_LR_CHANGE,
                     description=', '.join(changes_str))


def delete(clr):
    create_event(loan_rule_id=clr.id, event=CirculationEvent.EVENT_LR_DELETE)
    clr.delete()


schema = {}
