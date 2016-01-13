from invenio.modules.circulation.signals import (try_action_signal,
                                                 run_action_signal,
                                                 convert_params,
                                                 apis)


def _try_action(action, data):
    import invenio.modules.circulation.api.circulation as api
    from invenio.modules.circulation.api.utils import ValidationExceptions
    from invenio.modules.circulation.views.utils import filter_params

    actions = {'loan': api.try_loan_items,
               'request': api.try_request_items,
               'return': api.try_return_items}

    try:
        filter_params(actions[action], **data)
        res = True
    except KeyError:
        res = None
    except ValidationExceptions as e:
        res = [(ex[0], str(ex[1])) for ex in e.exceptions]

    return {'name': 'circulation', 'result': res}


def _run_action(action, data):
    import invenio.modules.circulation.api.circulation as api
    from invenio.modules.circulation.api.utils import ValidationExceptions
    from invenio.modules.circulation.views.utils import filter_params

    actions = {'loan': api.loan_items,
               'request': api.request_items,
               'return': api.return_items}

    filter_params(actions[action], **data)

    return {'name': 'circulation', 'result': _get_message(action, data)}


def _convert_params(action, data):
    import invenio.modules.circulation.models as models

    user = None
    if 'user' in data:
        user = data['user']
        if isinstance(user, list) and len(user) > 0:
            user = models.CirculationUser.get(user[0])

    items = [models.CirculationItem.get(x) for x in data['items']]

    return {'name': 'circulation', 'result': {'user': user, 'items': items}}


def _get_message(action, data):
    if action == 'loan':
        lm = 'The item(s): {0} were successfully loaned to the user: {1}.'
        return lm.format(', '.join(x.barcode for x in data['items']),
                                   data['user'].ccid)
    elif action == 'request':
        rm = 'The item(s): {0} were successfully requested by the user: {1}.'
        return rm.format(', '.join(x.barcode for x in data['items']),
                                   data['user'].ccid)
    elif action == 'return':
        items = data['items']
        rm = 'The item(s): {0} where successfully returned.'
        return rm.format(', '.join(x.barcode for x in data['items']))


def _apis(entity, data):
    import invenio.modules.circulation.api as api

    apis = {'item': api.item, 'loan_cycle': api.loan_cycle, 'user': api.user,
            'event': api.event, 'loan_rule': api.loan_rule,
            'location': api.location, 'mail_template': api.mail_template}

    return apis.get(entity)


try_action_signal.connect(_try_action)
run_action_signal.connect(_run_action)
convert_params.connect(_convert_params)
apis.connect(_apis)
