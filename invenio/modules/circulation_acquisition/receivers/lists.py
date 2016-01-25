from invenio.modules.circulation.signals import (lists_overview,
                                                 lists_class)


def _lists_overview(sender, data):
    return {'name': 'acquisition_lists',
            'priority': 1.0,
            'result': [('Purchase Requests', 'requested_purchase'),
                       ('Ordered Purchase Requests', 'ordered_purchase'),
                       ('Acquisition Requests', 'requested_acquisition'),
                       ('Ordered Acquisition Requests',
                        'ordered_acquisition')]}


def _lists_class(link, data):
    from invenio.modules.circulation_acquisition.lists.requested_acquisitions import (
            RequestedAcquisition)
    from invenio.modules.circulation_acquisition.lists.ordered_acquisitions import (
            OrderedAcquisition)
    from invenio.modules.circulation_acquisition.lists.requested_purchase import (
            RequestedPurchase)
    from invenio.modules.circulation_acquisition.lists.ordered_purchase import (
            OrderedPurchase)

    clazzes = {'requested_acquisition': RequestedAcquisition,
               'ordered_acquisition': OrderedAcquisition,
               'requested_purchase': RequestedPurchase,
               'ordered_purchase': OrderedPurchase}

    return {'name': 'acquisition_lists', 'result': clazzes.get(link)}

lists_overview.connect(_lists_overview)
lists_class.connect(_lists_class)
