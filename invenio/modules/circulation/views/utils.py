import datetime


def get_name_link_class(entities, entity):
    for _name, _link, clazz in entities:
        if _link == entity:
            return _name, _link, clazz
    else:
        raise Exception('Unknown entity: {0}'.format(entity))


def datetime_serial(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
