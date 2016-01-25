from invenio.modules.circulation.signals import item_returned


def _item_returned(sender, data):
    import invenio.modules.circulation_acquisition.models as models
    import invenio.modules.circulation_acquisition.api as api

    item_id = data
    res = models.AcquisitionLoanCycle.search('item_id:{0}'.format(item_id))

    if res and len(res) == 1:
        api.acquisition.return_acquisition(res[0])
        return {'name': 'acquisition', 'result': True}

    return {'name': 'acquisition', 'result': None}


item_returned.connect(_item_returned)
