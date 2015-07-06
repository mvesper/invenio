from invenio.modules.circulation.models import CirculationLoanCycle
from invenio.modules.circulation.configs.config_utils import DateManager
from invenio.modules.circulation.configs.config_utils import ConfigBase
from invenio.modules.circulation.configs.config_utils import create_event


class ReturnConfig(ConfigBase):
    new_status = 'finished'

    def run(self, _storage, clc, **kwargs):
        create_event(_storage, 'return', clc.user, clc.item, clc.library, clc)


class CancelConfig(ConfigBase):
    new_status = 'canceled'

    def run(self, _storage, clc, reason, **kwargs):
        create_event(_storage, 'cancel', clc.user, clc.item, clc.library, clc,
                     reason=reason)


class WaitlistConfig(ConfigBase):
    def run(self, _storage=None,
            _caller=None, _called=None,
            **kwargs):
        # We need some stuff first
        _uuid = _caller.uuid
        first_user = _called.user
        issued_date = _called.issued_date

        # Now we need to find the next blocking thing.
        # We therefore need a time stamp
        def check_clcs(clc):
            return (clc.issued_date < issued_date and
                    clc.current_status not in ['finished', 'canceled'] and
                    clc.uuid != _uuid)

        lcs = filter(check_clcs,
                     CirculationLoanCycle.search(item=_caller.item))

        start_date = _called.desired_start_date
        end_date = _called.desired_end_date

        requested_dates = [(lc.start_date, lc.end_date) for lc in lcs]
        _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                      requested_dates)

        # We then update the dates accordingly :)
        if _start < _called.start_date:
            if _start < _called.desired_start_date:
                _called.start_date = _called.desired_start_date
            else:
                _called.start_date = _start

        if _end > _called.end_date:
            if _end > _called.desired_end_date:
                _called.end_date = _called.desired_end_date
            else:
                _called.end_date = _end

        create_event(_storage, 'waitlist_updated',
                     _called.user, _called.item, _called.library, _called,
                     _called.start_date, _called.end_date)
        _storage.append(_called)

        return 1


loan_cycle_config = {
    "on_loan":
        {
            "return": ReturnConfig,
            "_update_waitlist": WaitlistConfig
        },
    "requested":
        {
            "cancel": CancelConfig,
            "_update_waitlist": WaitlistConfig
        },
    "finished": {},
    "canceled": {}
}
