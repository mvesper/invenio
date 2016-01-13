# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Signal receivers for workflows."""

import json

from invenio.base import signals
from invenio.base.scripts.database import create, drop, recreate


def create_circulation_indices(sender, **kwargs):
    from invenio.modules.circulation.models import entities
    from invenio.modules.circulation.mappings import mappings
    for name, __, cls in filter(lambda x: x[0] != 'Record', entities):
        mapping = mappings.get(name, {})
        index = cls.__tablename__
        cls._es.indices.delete(index=index, ignore=404)
        cls._es.indices.create(index=index, body=mapping)


def delete_circulation_indices(sender, **kwargs):
    from invenio.modules.circulation.models import entities
    for _, __, cls in filter(lambda x: x[0] != 'Record', entities):
        cls._es.indices.delete(index=cls.__tablename__, ignore=404)


signals.pre_command.connect(delete_circulation_indices, sender=drop)
signals.pre_command.connect(create_circulation_indices, sender=create)
signals.pre_command.connect(delete_circulation_indices, sender=recreate)
signals.pre_command.connect(create_circulation_indices, sender=recreate)
