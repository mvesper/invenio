from invenio.modules.circulation.signals import user_current_holds

def _user_current_holds(sender, data):
    import json
    import invenio.modules.circulation_acquisition.models as models

    from flask import render_template
    from invenio.modules.circulation_acquisition.api.utils import (
            _get_cal_heatmap_dates, _get_cal_heatmap_range)

    def make_dict(clc):
        return {'clc': clc,
                'cal_data': json.dumps(_get_cal_heatmap_dates([clc.item])),
                'cal_range': _get_cal_heatmap_range([clc.item])}

    user_id = data
    SL = models.AcquisitionLoanCycle.STATUS_ON_LOAN
    SR = models.AcquisitionLoanCycle.STATUS_REQUESTED
    SO = models.AcquisitionLoanCycle.STATUS_ORDERED

    query = 'user_id:{0} current_status:{1}'.format(user_id, SL)
    current_holds = [make_dict(clc) for clc
                     in models.AcquisitionLoanCycle.search(query)]

    query = 'user_id:{0} current_status:{1}'.format(user_id, SR)
    requested_holds = [make_dict(clc) for clc
                       in models.AcquisitionLoanCycle.search(query)]

    query = 'user_id:{0} current_status:{1}'.format(user_id, SO)
    ordered_holds = [make_dict(clc) for clc
                       in models.AcquisitionLoanCycle.search(query)]

    return {'name': 'acquisition', 'priority': 0.7,
            'result': [render_template('user/acquisition_current_holds.html',
                                       holds=current_holds),
                       render_template('user/acquisition_requested_holds.html',
                                       holds=requested_holds),
                       render_template('user/acquisition_ordered_holds.html',
                                       holds=ordered_holds)]}

user_current_holds.connect(_user_current_holds)
