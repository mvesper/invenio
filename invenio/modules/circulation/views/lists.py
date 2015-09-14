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

from flask import Blueprint, render_template

from invenio.modules.circulation.views.utils import get_name_link_class
from invenio.modules.circulation.circulation_lists import lists

blueprint = Blueprint('lists', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/lists')
def lists_overview():
    return render_template('lists/overview.html',
                           active_nav='lists', lists=lists)


@blueprint.route('/lists/<list_link>')
def list_result(list_link):
    _, link, clazz = get_name_link_class(lists, list_link)
    res = clazz.run()
    return render_template('lists/'+link+'.html', active_nav='lists', **res)
