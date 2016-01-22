from invenio.modules.circulation.signals import (
        circ_apis, run_action, try_action, convert_params)


def _get_action(action, try_action=False):
    import invenio.modules.circulation_ill.api as api

    actions = {'cancel_ill_request': (api.ill, 'cancel_ill_request'),
               'request_ill_extension': (api.ill, 'request_ill_extension'),
               'lose_ill': (api.ill, 'lose_ill')}

    try_action = 'try_' if try_action else ''

    _api, func_name = actions[action]

    return getattr(_api, try_action + func_name)


def _try_action(action, data):
    from invenio.modules.circulation.api.utils import ValidationExceptions
    from invenio.modules.circulation.views.utils import filter_params

    try:
        filter_params(_get_action(action, True), **data)
        res = True
    except KeyError:
        res = None
    except ValidationExceptions as e:
        res = [(ex[0], str(ex[1])) for ex in e.exceptions]

    return {'name': 'ill', 'result': res}


def _run_action(action, data):
    from invenio.modules.circulation.views.utils import filter_params

    try:
        filter_params(_get_action(action), **data)
        res = _get_message(action, data)
    except KeyError:
        res = None

    return {'name': 'ill', 'result': res}


def _get_message(action, data):
    return 'success'


def _apis(entity, data):
    import invenio.modules.circulation_ill.api as api

    apis = {'ill_loan_cycle': api.ill}

    return {'name': 'ill', 'result': apis.get(entity)}


def _convert_params(entity, data):
    import invenio.modules.circulation_ill.models as models

    try:
        ill_lc = models.IllLoanCycle.get(data['ill_lc_id'])
    except Exception:
        ill_lc = None

    res = {'ill_lc': ill_lc}

    return {'name': 'ill', 'result': res}


circ_apis.connect(_apis)
try_action.connect(_try_action)
run_action.connect(_run_action)
convert_params.connect(_convert_params)
