# coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
bibcirculation database models.
"""
import jsonpickle
import importlib
import elasticsearch
import sqlalchemy

from copy import deepcopy

from invenio.modules.records.models import RecordMetadata
from invenio.base.wrappers import lazy_import
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager


class CirculationPickleHandler(jsonpickle.handlers.BaseHandler):
    def _get_class(self, string):
        module_name, class_name = string.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return module.__getattribute__(class_name)

    def flatten(self, obj, data):
        data['id'] = obj.id
        """
        for key, value in obj.__dict__.items():
            if type(value) == sqlalchemy.orm.state.InstanceState:
                continue
            data[key] = value
        """
        return data

    def restore(self, obj):
        cls = self._get_class(obj['py/object'])
        return cls.get(obj['id'])


class CirculationObject(object):
    _es = elasticsearch.Elasticsearch()

    def __str__(self):
        try:
            return "{0}('{1}')".format(self.__class__.__name__, self.id)
        except AttributeError:
            return "{0}()".format(self.__class__.__name__)

    def __repr__(self):
        try:
            return "{0}('{1}')".format(self.__class__.__name__, self.id)
        except AttributeError:
            return "{0}()".format(self.__class__.__name__)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    @classmethod
    def new(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj

    @classmethod
    def get_all(cls):
        return [cls.get(x.id) for x in cls.query.all()]

    @classmethod
    def get(cls, id):
        obj = deepcopy(cls.query.get(id))
        data = jsonpickle.decode(obj._data)
        data['id'] = id

        for key, func in cls._construction_schema.items():
            try:
                obj.__setattr__(key, func(data))
            except AttributeError:
                pass

        return obj

        """
        data = deepcopy(cls.query.get(id)._data)
        _obj = cls(**jsonpickle.decode(data))
        _obj.id = id

        obj = cls()
        for key, func in cls._construction_schema.items():
            try:
                obj.__setattr__(key, func(_obj))
            except AttributeError:
                pass

        return obj
        """

    @classmethod
    @session_manager
    def delete_all(cls):
        cls.query.delete()
        cls._es.indices.delete(index=cls.__tablename__)
        cls._es.indices.create(index=cls.__tablename__)

    @session_manager
    def delete(self):
        db.session.delete(self)
        self._es.delete(index=self.__tablename__,
                        doc_type=self.__tablename__,
                        id=self.id)

    @classmethod
    def search(cls, **kwargs):
        queries = []
        for key, value in kwargs.items():
            queries.append({'match': {key: cls._encode(value)}})
        query = {'query': {'bool': {'must': queries}}}
        res = cls._es.search(index=cls.__tablename__, body=query)
        return [cls.get(x['_id']) for x in res['hits']['hits']]

    @session_manager
    def save(self):
        """Save object to persistent storage."""
        db_data, es_data = {}, {}
        for key, value in self.__dict__.items():
            if key not in ['_data', '_sa_instance_state']:
                db_data[key] = value
                es_data[key] = self._encode(value)

        #import pdb; pdb.set_trace()
        self._data = jsonpickle.encode(db_data)
        db.session.add(self)
        if not hasattr(self, 'id') or self.id is None:
            db.session.flush()

        es_data['id'] = self.id
        self._es.index(index=self.__tablename__,
                       doc_type=self.__tablename__,
                       id=self.id,
                       body=es_data)


    # Circulation functions
    def get_available_functions(self):
        return sorted(self._config[self.current_status].keys())

    def get_function_parameters(self, function_name, status=None):
        status = status if status else self.current_status
        return self._config[status][function_name].parameters

    def validate_run(self, function_name, **kwargs):
        action_obj = self._get_action_obj(self.current_status, function_name)
        action_obj.validate(**kwargs)

    def run(self, function_name, **kwargs):
        _save = True if '_storage' not in kwargs else False
        _storage = kwargs.pop('_storage', [])

        action_obj = self._get_action_obj(self.current_status, function_name)
        action_obj.validate(**kwargs)
        ret = action_obj.run(_storage=_storage, **kwargs)

        try:
            self.current_status = action_obj.new_status
        except AttributeError:
            pass

        try:
            for funcs, obj, func_name in self.callbacks[:]:
                if function_name in funcs:
                    try:
                        res = obj.run(func_name, _storage=_storage,
                                      _caller=self, _called=obj, **kwargs)
                        if res == 1:
                            break
                    except KeyError:
                        pass
        except AttributeError:
            pass

        _storage.append(self)

        if _save:
            for obj in _storage:
                obj.save()

        return ret

    def _get_action_obj(self, status, function_name):
        return self._config[status][function_name]()

    @classmethod
    def _encode(cls, value):
        if isinstance(value, dict):
            return {key: cls._encode(val) for key, val in value.items()}
        elif isinstance(value, list):
            return [cls._encode(val) for val in value]
        elif isinstance(value, tuple):
            return [cls._encode(val) for val in value]
        elif isinstance(value, CirculationObject):
            return value.id
        else:
            return value

    def _jsonify(self, value):
        if isinstance(value, dict):
            res = {}
            for key, val in value.items():
                res[key] = self._jsonify(val)
            return res
        elif isinstance(value, (list, tuple)):
            return [self._jsonify(val) for val in value]
        else:
            try:
                return value.jsonify()
            except AttributeError:
                return value

    def jsonify(self):
        res = {}
        for key, value in self.__dict__.items():
            if key == '_sa_instance_state':
                continue
            res[key] = self._jsonify(value)
        return res

    def pickle(self):
        return jsonpickle.encode(self)


class CirculationRecord(CirculationObject):
    _construction_schema = {'id': lambda x: x['id'],
                            'title': lambda x: x['title']['title'],
                            'abstract': lambda x: x['abstract']['expansion'],
                            'authors': lambda x: [{'name': y['full_name'], 'foo': 'bar'} for y in x['authors']],
                            'items': lambda x: CirculationItem.search(record=x['id'])}
    _json_schema = {'type': 'object',
                    'title': 'Record',
                    'properties': {
                        'id': {'type': 'integer'},
                        'title': {'type': 'string'},
                        'abstract': {'type': 'string', 'format': 'textarea'},
                        'authors': {
                            'type': 'array',
                            'format': 'table',
                            'items': {
                                'type': 'object',
                                'title': 'Author',
                                'properties': {
                                        'name': {'type': 'string'}
                                    }
                                }
                            },
                        'items': {
                            'type': 'array',
                            'format': 'table',
                            'items': {
                                'type': 'object',
                                'title': 'Item',
                                'properties': {
                                        'id': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                   }


    @classmethod
    def new(cls, **kwargs):
        raise Exception('CirculationRecord is a Wrapper class for Record.')

    @classmethod
    def get_all(cls):
        return [cls.get(x.id) for x in RecordMetadata.query.all()]

    @classmethod
    def get(cls, id):
        json = RecordMetadata.query.get(id).json
        json['id'] = id

        obj = CirculationRecord()
        for key, func in cls._construction_schema.items():
            try:
                obj.__setattr__(key, func(json))
            except AttributeError:
                pass

        return obj

    @classmethod
    def delete_all(cls):
        raise Exception('CirculationRecord is a Wrapper class for Record.')

    def delete(self):
        raise Exception('CirculationRecord is a Wrapper class for Record.')

    @classmethod
    def search(cls, **kwargs):
        from invenio.modules.search.api import SearchEngine
        query = ' '.join(['{0}:{1}'.format(key, val)
                          for key, val in kwargs.items()])
        return [cls.get(x) for x in SearchEngine(query).search()]

    @session_manager
    def save(self):
        raise Exception('CirculationRecord is a Wrapper class for Record.')


class CirculationItem(CirculationObject, db.Model):
    __tablename__ = 'circulation_item'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.item_config.item_config'))
    _construction_schema = {'id': lambda x: x['id'],
                            'isbn': lambda x: x['isbn'],
                            'barcode': lambda x: x['barcode'],
                            'record': lambda x: x['record'],
                            'current_status': lambda x: x['current_status'],
                            'allowed_loan_period': lambda x: x['allowed_loan_period']}
    _json_schema = {'type': 'object',
                    'title': 'Item',
                    'properties': {
                        'id': {'type': 'integer'},
                        'isbn': {'type': 'string'},
                        'barcode': {'type': 'string'},
                        'record': {'type': 'integer'},
                        'current_status': {'type': 'string'},
                        'allowed_loan_period': {'type': 'integer'},
                        }
                   }


class CirculationLoanCycle(CirculationObject, db.Model):
    __tablename__ = 'circulation_loan_cycle'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.loan_cycle_config.loan_cycle_config'))
    _construction_schema = {'id': lambda x: x['id'],
                            'current_status': lambda x: x['current_status'],
                            'item': lambda x: x['item'],
                            'library': lambda x: x['library'],
                            'user': lambda x: x['user'],
                            'start_date': lambda x: x['start_date'],
                            'end_date': lambda x: x['end_date'],
                            'date_issued': lambda x: x['date_issued']}
    _json_schema = {'type': 'object',
                    'title': 'User',
                    'properties': {
                        'id': {'type': 'integer'},
                        'current_status': {'type': 'string'},
                        'item': {'type': 'string'},
                        'library': {'type': 'string'},
                        'user': {'type': 'string'},
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                        'date_issued': {'type': 'string'},
                        }
                   }


class CirculationUser(CirculationObject, db.Model):
    __tablename__ = 'circulation_user'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.user_config.user_config'))
    _construction_schema = {'id': lambda x: x['id'],
                            'current_status': lambda x: x['current_status'],
                            'ccid': lambda x: x['ccid'],
                            'name': lambda x: x['name']}
    _json_schema = {'type': 'object',
                    'title': 'User',
                    'properties': {
                        'id': {'type': 'integer'},
                        'ccid': {'type': 'string'},
                        'name': {'type': 'string'}
                        }
                   }

class CirculationLibrary(CirculationObject, db.Model):
    __tablename__ = 'circulation_library'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _construction_schema = {'id': lambda x: x['id'],
                            'name': lambda x: x['name']}
    _json_schema = {'type': 'object',
                    'title': 'Library',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        }
                   }


class CirculationTask(CirculationObject, db.Model):
    __tablename__ = 'circulation_task'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _construction_schema = {'id': lambda x: x['id']}
    _json_schema = {'type': 'object',
                    'title': 'Task',
                    'properties': {
                        'id': {'type': 'integer'},
                        }
                   }


class CirculationEvent(CirculationObject, db.Model):
    __tablename__ = 'circulation_event'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _construction_schema = {'id': lambda x: x['id']}
    _json_schema = {'type': 'object',
                    'title': 'Event',
                    'properties': {
                        'id': {'type': 'integer'},
                        }
                   }


class CirculationMailTemplate(CirculationObject, db.Model):
    __tablename__ = 'circulation_mail_template'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _construction_schema = {'id': lambda x: x['id'],
                            'template_name': lambda x: x['template_name'],
                            'subject': lambda x: x['subject'],
                            'header': lambda x: x['header'],
                            'content': lambda x: x['content']}
    _json_schema = {'type': 'object',
                    'title': 'Mail Template',
                    'properties': {
                        'id': {'type': 'integer'},
                        'template_name': {'type': 'string'},
                        'subject': {'type': 'string'},
                        'header': {'type': 'string'},
                        'content': {'type': 'string',
                                    'format': 'textarea',
                                    'options': {'expand_height': True}},
                        }
                   }


jsonpickle.handlers.registry.register(CirculationItem,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationLoanCycle,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationUser,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationLibrary,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationTask,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationEvent,
                                      CirculationPickleHandler)
jsonpickle.handlers.registry.register(CirculationMailTemplate,
                                      CirculationPickleHandler)

# Display Name , link name, entity
entities = [('Record', 'record', CirculationRecord),
            ('Item', 'item', CirculationItem),
            ('Loan Cycle', 'loan_cycle', CirculationLoanCycle),
            ('User', 'user', CirculationUser),
            ('Library', 'library', CirculationLibrary),
            ('Task', 'task', CirculationTask),
            ('Event', 'event', CirculationEvent),
            ('Mail Template', 'mail_template', CirculationMailTemplate)]
