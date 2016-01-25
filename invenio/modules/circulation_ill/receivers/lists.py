from invenio.modules.circulation.signals import (lists_overview,
                                                 lists_class)


def _lists_overview(sender, data):
    return {'name': 'ill_lists',
            'priority': 0.75,
            'result': [('Requested Inter Library Loans', 'requested_ills'),
                       ('Confirmed Inter Library Loans', 'confirmed_ills'),
                       ('Inter Library Loans Extension', 'extension_ills')]}


def _lists_class(link, data):
    from invenio.modules.circulation_ill.lists.requested_ills import (
            RequestedIlls)
    from invenio.modules.circulation_ill.lists.confirmed_ills import (
            ConfirmedIlls)
    from invenio.modules.circulation_ill.lists.extension_ills import (
            ExtensionIlls)

    clazzes = {'requested_ills': RequestedIlls,
               'confirmed_ills': ConfirmedIlls,
               'extension_ills': ExtensionIlls}

    return {'name': 'lists', 'result': clazzes.get(link)}

lists_overview.connect(_lists_overview)
lists_class.connect(_lists_class)
