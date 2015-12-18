import invenio.modules.circulation_ill.models as models

from flask import render_template


class RequestedIlls(object):
    @classmethod
    def entrance(cls):
        q = 'current_status:{0}'.format(models.IllLoanCycle.STATUS_REQUESTED)
        ill_clcs = models.IllLoanCycle.search(q)
        return render_template('lists/requested_ills.html', ill_clcs=ill_clcs,
                               active_nav='lists')
