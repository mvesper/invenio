import invenio.modules.circulation_acquisition.models as models

from flask import render_template


class RequestedPurchase(object):
    @classmethod
    def entrance(cls):
        q = 'current_status:{0} additional_statuses:{1}'
        q = q.format(models.AcquisitionLoanCycle.STATUS_REQUESTED,
                     models.AcquisitionLoanCycle.TYPE_PURCHASE)
        acquisition_clcs = models.AcquisitionLoanCycle.search(q)
        return render_template('lists/requested_acquisitions.html',
                               acquisition_clcs=acquisition_clcs,
                               confirmation_action='confirm',
                               confirmation_name='CONFIRM',
                               active_nav='lists')
