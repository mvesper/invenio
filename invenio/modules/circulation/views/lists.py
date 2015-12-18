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

import json

from flask import Blueprint, render_template

from invenio.modules.circulation.lists import get_circulation_lists

blueprint = Blueprint('lists', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')

titles = {'on_loan_pending_requests': 'Items on loan with pending requests',
          'on_shelf_pending_requests': 'Items on shelf with pending requests',
          'overdue_pending_requests': 'Overdue items with pending requests',
          'overdue_items': 'Overdue Items',
          'latest_loans': 'Latest Loans'}


@blueprint.route('/lists')
def lists_overview():
    lists = [(link, titles[link]) for link, _ in get_circulation_lists()]

    # Signal to get other entities
    from invenio.modules.circulation.signals import lists_overview as lo
    lists.extend([(link, title) for _, ill_lists in lo.send()
                  for link, title in ill_lists])

    return render_template('lists/overview.html',
                           active_nav='lists', lists=lists)


@blueprint.route('/lists/<list_link>')
def list_entrance(list_link):
    try:
        clazz = _get_class(list_link)
    except Exception:
        from invenio.modules.circulation.signals import lists_class as lc
        try:
            clazz = lc.send(list_link)[0][1]
        except IndexError:
            raise Exception('Unkown entity: {0}'.format(list_link))

    return clazz.entrance()


@blueprint.route('/lists/<list_link>/detail/')
@blueprint.route('/lists/<list_link>/detail/<query>')
def list_detail(list_link, query=None):
    try:
        clazz = _get_class(list_link)
    except Exception:
        from invenio.modules.circulation.signals import lists_class as lc
        try:
            clazz = lc.send(list_link)[0][1]
        except IndexError:
            raise Exception('Unkown entity: {0}'.format(list_link))

    try:
        data = json.loads(query)
    except Exception:
        data = {}

    return clazz.detail(**data)


def _get_class(link):
    for _link, clazz in get_circulation_lists():
        if link == _link:
            return clazz
    raise Exception
