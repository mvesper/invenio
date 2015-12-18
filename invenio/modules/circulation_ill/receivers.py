from invenio.modules.circulation.signals import *
from invenio.base import signals
from invenio.base.scripts.database import create, drop, recreate


def save_circulation_event_entity(sender):
    return ['ill_loan_cycle_id']


def get_circulation_event_entity(sender):
    return ['ill_loan_cycle_id']


def get_ill_entities(sender):
    return [('ILL Loan Cycle', 'ill_loan_cycle')]


def ill_search(sender):
    import invenio.modules.circulation_ill.models as models

    return (models.IllLoanCycle, 'ill_entities/ill_loan_cycle.html')


def get_entity_info(sender):
    import invenio.modules.circulation_ill.models as models
    import invenio.modules.circulation_ill.aggregators as aggregators

    return (models.IllLoanCycle,
            aggregators.IllLoanCycleAggregator,
            'ill_entities/ill_loan_cycle_detail.html')


def get_entity_new(sender):
    import invenio.modules.circulation_ill.aggregators as aggregators

    return aggregators.IllLoanCycleAggregator


def get_entity_create(sender):
    import invenio.modules.circulation_ill.api.ill as api

    return ('IllLoanCycle', api)


def get_entity_update(sender):
    import invenio.modules.circulation_ill.models as models
    import invenio.modules.circulation_ill.api.ill as api

    return ('IllLoanCycle', models.IllLoanCycle, api)


def get_entity_delete(sender):
    import invenio.modules.circulation_ill.models as models
    import invenio.modules.circulation_ill.api.ill as api

    return ('IllLoanCycle', models.IllLoanCycle, api)


def get_ill_lists(sender):
    return [('requested_ills', 'Requested Inter Library Loans'),
            ('confirmed_ills', 'Confirmed Inter Library Loans')]


def get_ill_class(sender):
    if sender == 'requested_ills':
        from invenio.modules.circulation_ill.lists.requested_ills import (
                RequestedIlls)
        return RequestedIlls
    elif sender == 'confirmed_ills':
        from invenio.modules.circulation_ill.lists.confirmed_ills import (
                ConfirmedIlls)
        return ConfirmedIlls


def get_returned_items_ill_clc(item_id):
    import invenio.modules.circulation_ill.models as models
    import invenio.modules.circulation_ill.api as api

    for ill_clc in models.IllLoanCycle.search('item_id:{0}'.format(item_id)):
        api.ill.return_ill(ill_clc)


def get_current_ill_holds(user_id):
    import invenio.modules.circulation_ill.models as models
    from invenio.modules.circulation_ill.api.utils import _get_current

    sl = models.IllLoanCycle.STATUS_ON_LOAN
    sr = models.IllLoanCycle.STATUS_REQUESTED
    headers = ['Title', 'Start Date', 'End Date']

    cl_actions = [('ill_extend', 'EXTEND LOAN')]
    cr_actions = [('ill_cancel', 'CANCEL REQUEST')]

    return {'Ill Current Loans': {'data': _get_current(user_id, sl),
                                  'table_headers': headers,
                                  'actions': cl_actions},
            'Ill Current Requests': {'data': _get_current(user_id, sr),
                                     'table_headers': headers,
                                     'actions': cr_actions}}


def current_holds_ill_cancel(action, data):
    import invenio.modules.circulation_ill.models as models
    from invenio.modules.circulation_ill.api.ill import cancel_ill_request

    ill_clc = models.IllLoanCycle.get(data['clc_id'])
    cancel_ill_request(ill_clc)

    msg = ('The inter library request on the item: {0}, '
           'was successfully canceled')
    return msg.format(ill_clc.item.record.title)


# TODO: The sender should be the class itself, but that leads to some errors
# with SQLAlchemy ~.~
save_entity.connect(save_circulation_event_entity, 'CirculationEvent')
get_entity.connect(get_circulation_event_entity, 'CirculationEvent')
entities_overview.connect(get_ill_entities)
entities_hub_search.connect(ill_search, 'ill_loan_cycle')
entity.connect(get_entity_info, 'ill_loan_cycle')
entity_new.connect(get_entity_new, 'ill_loan_cycle')
entity_create.connect(get_entity_create, 'ill_loan_cycle')
entity_update.connect(get_entity_update, 'ill_loan_cycle')
entity_delete.connect(get_entity_delete, 'ill_loan_cycle')

lists_overview.connect(get_ill_lists)
lists_class.connect(get_ill_class)

item_returned.connect(get_returned_items_ill_clc)

user_current_holds.connect(get_current_ill_holds)
user_current_holds_action.connect(current_holds_ill_cancel, 'ill_cancel')


def create_circulation_ill_indices(sender, **kwargs):
    from invenio.modules.circulation_ill.models import entities
    from invenio.modules.circulation_ill.mappings import mappings
    for name, __, cls in filter(lambda x: x[0] != 'Record', entities):
        mapping = mappings.get(name, {})
        index = cls.__tablename__
        cls._es.indices.delete(index=index, ignore=404)
        cls._es.indices.create(index=index, body=mapping)


def delete_circulation_ill_indices(sender, **kwargs):
    from invenio.modules.circulation_ill.models import entities
    for _, __, cls in filter(lambda x: x[0] != 'Record', entities):
        cls._es.indices.delete(index=cls.__tablename__, ignore=404)


signals.pre_command.connect(delete_circulation_ill_indices, sender=drop)
signals.pre_command.connect(create_circulation_ill_indices, sender=create)
signals.pre_command.connect(delete_circulation_ill_indices, sender=recreate)
signals.pre_command.connect(create_circulation_ill_indices, sender=recreate)
