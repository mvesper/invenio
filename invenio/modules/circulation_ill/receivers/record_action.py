from invenio.modules.circulation.signals import record_actions


def _record_actions(sender, data):
    from flask import render_template

    res = render_template('search/request_ill.html', **data)
    return {'name': 'circulation_ill', 'priority': 0.7, 'result': res}


record_actions.connect(_record_actions)
