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

"""Circulation interface."""

import json

from flask import Blueprint, render_template, request, redirect, flash

from invenio.modules.circulation.views.utils import send_signal


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/', methods=['GET'])
@blueprint.route('/circulation/<search_string>', methods=['GET'])
def circulation_search(search_string=None):
    from invenio.modules.circulation.signals import circulation_current_state

    data = send_signal(circulation_current_state, None, search_string)[0]

    if data['search']:
        from invenio.modules.circulation.signals import circulation_search

        new_url = send_signal(circulation_search, None, data)[0]()
        return redirect('/circulation/circulation/' + new_url)
    else:
        from invenio.modules.circulation.signals import circulation_state

        content = send_signal(circulation_state, None, data)[0]()
        return render_template('circulation/circulation.html',
                               active_nav='circulation', content=content)


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    from invenio.modules.circulation.signals import run_action, convert_params

    data = json.loads(request.get_json())

    res = send_signal(convert_params, data['action'], data)
    for key, value in reduce(lambda x, y: dict(x, **y), res).items():
        data[key] = value

    message = send_signal(run_action, data['action'], data)[0]

    flash(message)
    return ('', 200)


@blueprint.route('/api/circulation/try_action', methods=['POST'])
def api_circulation_try_action():
    from invenio.modules.circulation.signals import try_action, convert_params

    data = json.loads(request.get_json())

    res = send_signal(convert_params, data['action'], data)
    for key, value in reduce(lambda x, y: dict(x, **y), res).items():
        data[key] = value

    return json.dumps(send_signal(try_action, data['action'], data)[0])
