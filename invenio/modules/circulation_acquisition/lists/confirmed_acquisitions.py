import invenio.modules.circulation_acquisition.models as models

from flask import render_template


class ConfirmedAcquisition(object):
    @classmethod
    def entrance(cls):
        q = 'current_status:{0}'.format(models.AcquisitionLoanCycle.STATUS_ORDERED)
        acquisition_clcs = models.AcquisitionLoanCycle.search(q)
        return render_template('lists/confirmed_acquisitions.html', acquisition_clcs=acquisition_clcs,
                               active_nav='lists')
