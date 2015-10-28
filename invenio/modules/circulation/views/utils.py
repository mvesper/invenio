import datetime
import json
import inspect

from flask import request


def extract_params(func):
    _args = inspect.getargspec(func).args

    def wrap():
        data = json.loads(request.get_json())
        return func(**{arg_name: data[arg_name] for arg_name in _args})

    wrap.func_name = func.func_name
    return wrap


def get_name_link_class(entities, entity):
    for _name, _link, clazz in entities:
        if _link == entity:
            return _name, _link, clazz
    else:
        raise Exception('Unknown entity: {0}'.format(entity))


def datetime_serial(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
