# -*- coding: utf-8 -*-
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

# General imports.
import uuid
import jsonpickle
import importlib
import elasticsearch

from copy import deepcopy

from invenio.base.wrappers import lazy_import
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager


class CirculationPickleHandler(jsonpickle.handlers.BaseHandler):
    def _get_class(self, string):
        module_name, class_name = string.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return module.__getattribute__(class_name)

    def flatten(self, obj, data):
        data['uuid'] = obj.uuid
        return data

    def restore(self, obj):
        cls = self._get_class(obj['py/object'])
        return cls.get(obj['uuid'])


class CirculationObject(object):
    _es = elasticsearch.Elasticsearch()

    def __str__(self):
        try:
            return "{0}('{1}')".format(self.__class__.__name__, self.uuid)
        except AttributeError:
            return "{0}()".format(self.__class__.__name__)

    def __repr__(self):
        try:
            return "{0}('{1}')".format(self.__class__.__name__, self.uuid)
        except AttributeError:
            return "{0}()".format(self.__class__.__name__)

    def __init__(self, **kwargs):
        self.uuid = str(uuid.uuid4())
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    @classmethod
    def new(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj

    @classmethod
    def get_all(cls):
        return [cls.get(x.uuid) for x in cls.query.all()]

    @classmethod
    def get(cls, uuid):
        obj = deepcopy(cls.query.get(uuid))
        for key, value in jsonpickle.decode(obj._data).items():
            obj.__setattr__(key, value)
        return obj

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
                        id=self.uuid)

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
            if key not in ['_data', 'uuid', '_sa_instance_state']:
                db_data[key] = value
                es_data[key] = self._encode(value)

        self._es.index(index=self.__tablename__,
                       doc_type=self.__tablename__,
                       id=self.uuid,
                       body=es_data)

        self._data = jsonpickle.encode(db_data)
        db.session.add(self)

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
            return value.uuid
        else:
            return value

    def jsonify(self, methods=False):
        res = {key: self._encode(value)
               for key, value in self.__dict__.items()
               if key not in ['_data', 'uuid', '_sa_instance_state']}
        # TODO: only temporary
        if methods:
            try:
                res['methods'] = self.get_available_functions()
            except:
                res['methods'] = []

        return res


class CirculationItem(CirculationObject, db.Model):
    __tablename__ = 'circulation_item'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.item_config.item_config'))


class CirculationLoanCycle(CirculationObject, db.Model):
    __tablename__ = 'circulation_loan_cycle'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.loan_cycle_config.loan_cycle_config'))


class CirculationUser(CirculationObject, db.Model):
    __tablename__ = 'circulation_user'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)
    _config = lazy_import(('invenio.modules.circulation.'
                           'configs.user_config.user_config'))


class CirculationLibrary(CirculationObject, db.Model):
    __tablename__ = 'circulation_library'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)


class CirculationTask(CirculationObject, db.Model):
    __tablename__ = 'circulation_task'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)


class CirculationEvent(CirculationObject, db.Model):
    __tablename__ = 'circulation_event'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)


class CirculationMailTemplate(CirculationObject, db.Model):
    __tablename__ = 'circulation_mail_template'
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    _data = db.Column(db.LargeBinary)


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
