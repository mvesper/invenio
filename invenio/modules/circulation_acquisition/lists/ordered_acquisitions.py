import invenio.modules.circulation_acquisition.models as models

from flask import render_template


class OrderedAcquisition(object):
    @classmethod
    def entrance(cls):
        q = 'current_status:{0} additional_statuses:{1}'
        q = q.format(models.AcquisitionLoanCycle.STATUS_ORDERED,
                     models.AcquisitionLoanCycle.TYPE_ACQUISITION)
        acquisition_clcs = models.AcquisitionLoanCycle.search(q)
        return render_template('lists/requested_acquisitions.html',
                               acquisition_clcs=acquisition_clcs,
                               confirmation_action='receive',
                               confirmation_name='RECEIVE',
                               active_nav='lists')
