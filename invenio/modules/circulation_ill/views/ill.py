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
import datetime

import invenio.modules.circulation.models as circ_models
import invenio.modules.circulation_ill.models as models
import invenio.modules.circulation_ill.api as api

from flask import Blueprint, render_template, flash, request
from invenio_records.api import get_record

blueprint = Blueprint('ill', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='static')


@blueprint.route('/ill/request_ill/<user_id>')
@blueprint.route('/ill/request_ill/<user_id>/<record_id>')
def ill_request(user_id, record_id=0):
    rec = get_record(record_id) if record_id else {}
    data = {'record_id': record_id, 'user_id': user_id}

    try:
        data['title'] = rec['title_statement']['title']
    except Exception:
        pass

    try:
        data['isbn'] = rec['international_standard_book_number']
    except Exception:
        pass

    imprint = 'publication_distribution_imprint'

    try:
        date = 'date_of_publication_distribution'
        data['year'] = rec[imprint][0][date][0]
    except Exception:
        pass

    try:
        publisher = 'name_of_publisher_distributor'
        data['publisher'] = rec[imprint][0][publisher][0]
    except Exception:
        pass

    data['authors'] = []
    pn = 'personal_name'
    try:
        data['authors'].append(rec['main_entry_personal_name'][pn])
    except Exception:
        pass

    try:
        tmp = [x[pn] for x in rec['added_entry_personal_name']]
        data['authors'].extend(tmp)
    except Exception:
        pass

    data['authors'] = '; '.join(data['authors'])

    data['start_date'] = datetime.date.today().isoformat()
    data['end_date'] = datetime.date.today() + datetime.timedelta(weeks=4)

    return render_template('circulation_ill_request.html', **data)


def _create_record(data):
    from copy import copy
    from invenio_records.api import create_record

    data = copy(data)
    del data['record_id']

    authors = data['authors'].split(';')
    if authors:
        main_author = authors[0]
        added_authors = authors[1:]

    record = {'title_statement': {'title': data['title']},
              'international_standard_book_number': data['isbn'],
              'publication_distribution_imprint': [
                  {'date_of_publication_distribution': [data['year']],
                   'name_of_publisher_distributor': [data['publisher']]}],
              'main_entry_personal_name': {'personal_name': main_author},
              'added_entry_personal_name': [
                  {'personal_name': x} for x in added_authors]}

    return create_record(record)


@blueprint.route('/api/ill/create_ill_request/', methods=['POST'])
def create_ill_request():
    data = json.loads(request.get_json())

    user = circ_models.CirculationUser.get(data['user_id'])
    if data['record']['record_id']:
        record = circ_models.CirculationRecord.get(data['record']['record_id'])
    else:
        # TODO: It might make sense to mark the new record as temporary
        record = _create_record(data['record'])
        record = circ_models.CirculationRecord.get(record['control_number'])

    start_date = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d')
    comments = data['comments']
    delivery = data['delivery']

    api.ill.request_ill(user, record, start_date, end_date, delivery)

    flash('Successfully created an ill request.')
    return ('', 200)


@blueprint.route('/api/ill/perform_action/', methods=['POST'])
def perform_ill_action():
    actions = {'confirm': api.ill.confirm_ill_request,
               'decline': api.ill.decline_ill_request,
               'deliver': api.ill.deliver_ill,
               'cancel': api.ill.cancel_ill_request,
               'confirm_ill_extension': api.ill.confirm_ill_extension,
               'decline_ill_extension': api.ill.decline_ill_extension}
    msgs = {'confirm': 'confirmed', 'decline': 'declined',
            'deliver': 'delivered', 'cancel': 'canceled',
            'confirm_ill_extension': 'extended',
            'decline_ill_extension': 'not extended'}

    data = json.loads(request.get_json())
    action = data['action']
    ill_clc_id = data['ill_clc_id']

    ill_clc = models.IllLoanCycle.get(ill_clc_id)

    actions[action](ill_clc)

    flash('Successfully {0} the ill request {1}.'.format(msgs[action],
                                                         ill_clc_id))
    return ('', 200)
