from invenio.modules.circulation.signals import (entities_overview,
                                                 entities_hub_search,
                                                 entity,
                                                 entity_suggestions,
                                                 entity_aggregations,
                                                 entity_class,
                                                 entity_name,
                                                 get_entity,
                                                 save_entity)


def _entities_overview(sender, data):
    return {'name': 'acquisition_entity',
            'priority': 1.0,
            'result': [('Acquisition Loan Cycle', 'acquisition_loan_cycle')]}


def _entities_hub_search(sender, data):
    import invenio.modules.circulation_acquisition.models as models

    search = data

    models_entities = {'acquisition_loan_cycle': models.AcquisitionLoanCycle}

    entity = models_entities.get(sender)
    res = None
    if entity:
        res = (entity.search(search), 'entities/' + sender + '.html')

    return {'name': 'acquisition_entity', 'result': res}


def _entity(sender, data):
    import invenio.modules.circulation_acquisition.models as models

    id = data

    models_entities = {'acquisition_loan_cycle': models.AcquisitionLoanCycle}

    entity = models_entities.get(sender)
    res = entity.get(id) if entity else None

    return {'name': 'acquisition_entity', 'result': res}


def _entity_suggestions(entity, data):
    suggestions = {'acquisition_loan_cycle': [('item_id', 'item',
                                       ['id', 'record.title'],
                                      '/circulation/api/entity/search'),
                                      ('user_id', 'user',
                                       ['id', 'name'],
                                      '/circulation/api/entity/search')],
                                      }

    return {'name': 'acquisition_entity', 'result': suggestions.get(entity)}


def _entity_aggregations(entity, data):
    id = data

    res = None
    if entity == 'acquisition_loan_cycle':
        res = _get_loan_cycle_aggregations(id)

    return {'name': 'acquisition_entity', 'result': res}


def _get_loan_cycle_aggregations(id):
    return None


def _entity_class(entity, data):
    import invenio.modules.circulation_acquisition.models as models

    models = {'acquisition_loan_cycle': models.AcquisitionLoanCycle}

    return {'name': 'acquisition_entity', 'result': models.get(entity)}


def _entity_name(entity, data):
    names = {'acquisition_loan_cycle': 'Ill Loan Cycle'}

    return {'name': 'acquisition_entity', 'result': names.get(entity)}


def _get_entity(class_name, data):
    class_names = {'CirculationEvent': ['acquisition_loan_cycle_id']}
    return {'name': 'acquisition', 'result': class_names.get(class_name)}


def _save_entity(class_name, data):
    class_names = {'CirculationEvent': ['acquisition_loan_cycle_id']}
    return {'name': 'acquisition', 'result': class_names.get(class_name)}


entities_overview.connect(_entities_overview)
entities_hub_search.connect(_entities_hub_search)
entity.connect(_entity)
entity_suggestions.connect(_entity_suggestions)
entity_aggregations.connect(_entity_aggregations)
entity_class.connect(_entity_class)
entity_name.connect(_entity_name)
get_entity.connect(_get_entity)
save_entity.connect(_save_entity)
