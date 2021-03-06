# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012 CERN.
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
Test unit for the miscutil/importutils module.
"""

from invenio.testutils import InvenioTestCase

from invenio.importutils import autodiscover_modules
from invenio.testutils import make_test_suite, run_test_suite


class TestImportUtils(InvenioTestCase):
    """
    importutils TestSuite.
    """

    def test_autodiscover_modules(self):
        modules = autodiscover_modules(['invenio.bibformat_elements'], related_name_re='bfe_.+\.py')
        assert(len(modules) > 10)
        modules = autodiscover_modules(['invenio'], related_name_re='(.+)_config\.py')
        assert(len(modules) > 10)
        assert(None not in modules)
        modules = autodiscover_modules(['invenio.not_an_existing_folder'], related_name_re='foo_.+\.py')
        assert(len(modules) == 0)
        assert(None not in modules)
        modules = autodiscover_modules(['invenio.bibformat_elements'], related_name_re='not_an_existing_file_name_.+\.yp')
        assert(len(modules) == 0)
        assert(None not in modules)


TEST_SUITE = make_test_suite(TestImportUtils,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
