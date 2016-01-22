import invenio.modules.circulation_ill.models as models

from flask import render_template


class ExtensionIlls(object):
    @classmethod
    def entrance(cls):
        s = models.IllLoanCycle.STATUS_EXTENSION_REQUESTED
        q = 'additional_statuses:{0}'.format(s)
        ill_clcs = models.IllLoanCycle.search(q)
        return render_template('lists/extension_ills.html', ill_clcs=ill_clcs,
                               active_nav='lists')
