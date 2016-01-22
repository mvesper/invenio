from invenio.modules.circulation.signals import item_returned


def _item_returned(sender, data):
    import invenio.modules.circulation_ill.models as models
    import invenio.modules.circulation_ill.api as api

    item_id = data
    res = models.IllLoanCycle.search('item_id:{0}'.format(item_id))

    if res and len(res) == 1:
        api.ill.return_ill(res[0])
        return {'name': 'ill', 'result': True}

    return {'name': 'ill', 'result': None}


item_returned.connect(_item_returned)
