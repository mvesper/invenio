# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Circulation bundles."""

from __future__ import unicode_literals

from invenio.base.bundles import invenio as _i, jquery as _j, styles as _styles
from invenio.ext.assets import Bundle, RequireJSFilter

js = Bundle(
    "js/circulation/circulation_init.js",
    output="circulation.js",
    filters=RequireJSFilter(exclude=[_j, _i]),
    weight=51,
)

js1 = Bundle(
    "js/circulation/entity_init.js",
    output="entity.js",
    filters=RequireJSFilter(exclude=[_j, _i]),
    weight=51,
)


js2 = Bundle(
    "js/circulation/user_init.js",
    output="user.js",
    filters=RequireJSFilter(exclude=[_j, _i]),
    weight=51,
)

js3 = Bundle(
    "js/circulation/lists_init.js",
    output="lists.js",
    filters=RequireJSFilter(exclude=[_j, _i]),
    weight=51,
)

styles = Bundle(
    "vendors/jquery-ui/themes/redmond/jquery-ui.css",
    "css/other/cal-heatmap.css",
    "css/circulation/user.css",
    "vendors/typeahead.js-bootstrap3.less/typeahead.css",
    output="circulation.css",
    filters="cleancss",
    weight=51
)

"""
styles = Bundle(
    "css/deposit/form.css",
    "vendors/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.css",
    output="deposit.css",
    filters="cleancss",
    weight=51
)
"""
