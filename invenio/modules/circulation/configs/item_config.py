import datetime

from invenio.modules.circulation.configs.config_utils import ConfigBase
from invenio.modules.circulation.configs.config_utils import DateManager
from invenio.modules.circulation.configs.config_utils import DateException
from invenio.modules.circulation.configs.config_utils import email_notification
from invenio.modules.circulation.configs.config_utils import create_event
from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationUser)


class LoanConfig(ConfigBase):
    new_status = 'on_loan'
    parameters = ['item', 'user', 'library', 'start_date', 'end_date']

    """
    @log_event('loan', ['item', 'library', 'user',
                        'start_date', 'end_date', 'desired_end_date'])
    """
    @email_notification('item_loan')
    def run(self, _storage,
            item=None, user=None, library=None,
            start_date=None, end_date=None,
            waitlist=False,
            **kwargs):

        clc = CirculationLoanCycle(current_status='on_loan',
                                   item=item, library=library, user=user,
                                   start_date=start_date,
                                   end_date=self.end_date,
                                   date_issued=datetime.datetime.now())
        if waitlist:
            clc.desired_end_date = self.desired_end_date
            for blocking_clc in self.blocking_clcs:
                tmp = (('cancel', 'return'), clc, '_update_waitlist')
                try:
                    blocking_clc.callbacks.append(tmp)
                except AttributeError:
                    blocking_clc.callbacks = [tmp]
                _storage.append(blocking_clc)

        create_event(_storage, 'loan', user, item, library, clc,
                     start_date, self.end_date)
        _storage.append(clc)

    def check_item(self, item=None, **kwargs):
        if not item:
            raise Exception('A item is required to loan an item.')
        if isinstance(item, (list, tuple)):
            raise Exception('Only one item can be loaned.')
        if not isinstance(item, CirculationItem):
            raise Exception('The item must be of the type CirculationItem.')

    def check_user(self, user=None, **kwargs):
        if not user:
            raise Exception('A user is required to loan an item.')
        if isinstance(user, (list, tuple)):
            raise Exception('An item can only be loaned to one user.')
        if not isinstance(user, CirculationUser):
            raise Exception('The item must be of the type CirculationUser.')

    def check_library(self, library=None, **kwargs):
        pass

    def check_loan_period(self, item=None,
                          start_date=None, end_date=None,
                          waitlist=False,
                          **kwargs):
        if start_date is None or end_date is None:
            raise Exception('Start date and end date need to be specified.')
        desired_loan_period = end_date - start_date
        if desired_loan_period.days > item.allowed_loan_period:
            msg = ('The desired loan period ({0} days) exceeds '
                   'the allowed period of {1} days.')
            raise Exception(msg.format(desired_loan_period.days,
                                       item.allowed_loan_period))

        lcs = CirculationLoanCycle.search(item=item.id)
        lcs = filter(lambda x: x.current_status not in ['finished', 'canceled'],
                     lcs)
        requested_dates = [(lc.start_date, lc.end_date) for lc in lcs]
        _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                      requested_dates)
        self.start_date = _start
        self.desired_start_date = start_date

        self.end_date = _end
        self.desired_end_date = end_date

        if waitlist:
            if _start != start_date:
                raise DateException(DateManager
                                    .get_date_suggestions(requested_dates))

            self.blocking_clcs = [lc for lc in lcs
                                  if lc.start_date <= end_date <= lc.end_date]
        else:
            if _start != start_date or _end != end_date:
                raise DateException(DateManager
                                    .get_date_suggestions(requested_dates))


class LoseConfig(ConfigBase):
    new_status = 'missing'
    parameters = ['item']

    # @log_event('lose', ['item'])
    def run(self, _storage,
            item=None, **kwargs):
        clcs = CirculationLoanCycle.search(item=item, current_status='on_loan')
        clcs += CirculationLoanCycle.search(item=item,
                                            current_status='reserved')
        clcs += CirculationLoanCycle.search(item=item,
                                            current_status='overdue')
        for clc in clcs:
            clc.run('cancel', _storage=_storage, clc=clc, reason='lost')

        # This doesn't need an event, they will be logged in the clc

    def check_item(self, item=None, **kwargs):
        if not item:
            raise Exception('There needs to be an item')
        if isinstance(item, (list, tuple)):
            raise Exception('Only one item can be lost.')
        if not isinstance(item, CirculationItem):
            raise Exception('The item must be of the type CirculationItem.')


class RequestConfig(ConfigBase):
    parameters = ['item', 'user', 'library', 'start_date', 'end_date']

    """
    @log_event('request', ['item', 'library', 'user',
                           'start_date', 'end_date',
                           'desired_start_date', 'desired_end_date'])
    """
    @email_notification('item_request')
    def run(self, _storage,
            item=None, user=None, library=None,
            delivery='pick up', waitlist=False,
            start_date=None, end_date=None,
            **kwargs):

        clc = CirculationLoanCycle(current_status='requested',
                                   delivery=delivery,
                                   item=item, library=library, user=user,
                                   start_date=self.start_date,
                                   end_date=self.end_date,
                                   date_issued=datetime.datetime.now())

        if waitlist:
            try:
                clc.desired_start_date = self.desired_start_date
            except AttributeError:
                pass
            try:
                clc.desired_end_date = self.desired_end_date
            except AttributeError:
                pass
            for blocking_clc in self.blocking_clcs:
                tmp = (('cancel', 'return'), clc, '_update_waitlist')
                try:
                    blocking_clc.callbacks.append(tmp)
                except AttributeError:
                    blocking_clc.callbacks = [tmp]
                _storage.append(blocking_clc)

        create_event(_storage, 'request', user, item, library, clc,
                     self.start_date, self.end_date)
        _storage.append(clc)

    def check_item(self, item=None, **kwargs):
        if not item:
            raise Exception('A item is required to loan an item')
        if isinstance(item, (list, tuple)):
            raise Exception('Only one item can be requested.')
        if not isinstance(item, CirculationItem):
            raise Exception('The item must be of the type CirculationItem.')

    def check_user(self, user=None, **kwargs):
        if not user:
            raise Exception('A user is required to loan an item')
        if isinstance(user, (list, tuple)):
            raise Exception('An item can only be requested to one user.')
        if not isinstance(user, CirculationUser):
            raise Exception('The item must be of the type CirculationUser.')

    def check_library(self, library=None, **kwargs):
        pass

    def check_loan_period(self, item=None,
                          start_date=None, end_date=None,
                          waitlist=False,
                          **kwargs):
        if start_date is None or end_date is None:
            raise Exception('Start date and end date need to be specified')
        desired_loan_period = end_date - start_date
        if desired_loan_period.days > item.allowed_loan_period:
            msg = ('The desired request period ({0} days) exceeds '
                   'the allowed period of {1} days.')
            raise Exception(msg.format(desired_loan_period.days,
                                       item.allowed_loan_period))

        lcs = CirculationLoanCycle.search(item=item.id)
        lcs = filter(lambda x: x.current_status not in ['finished', 'canceled'],
                     lcs)
        requested_dates = [(lc.start_date, lc.end_date) for lc in lcs]
        try:
            _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                          requested_dates)
        except Exception:
            if waitlist:
                _start, _end = start_date, end_date

        self.start_date = _start
        self.desired_start_date = start_date

        self.end_date = _end
        self.desired_end_date = end_date

        if waitlist:
            self.blocking_clcs = [lc for lc in lcs
                                  if lc.desired_start_date <=
                                  start_date <=
                                  lc.desired_end_date]
            self.blocking_clcs += [lc for lc in lcs
                                   if lc.desired_start_date <=
                                   end_date <=
                                   lc.desired_end_date]
        else:
            if _start != start_date and _end != end_date:
                raise DateException(DateManager
                                    .get_date_suggestions(requested_dates))


class ReturnConfig(ConfigBase):
    new_status = 'on_shelf'
    parameters = ['item']

    # @log_event('return', ['item'])
    def run(self, _storage,
            item=None, **kwargs):
        clc = CirculationLoanCycle.search(item=item,
                                          current_status='on_loan')[0]
        clc.run('return', _storage=_storage, clc=clc)

        # create_event(_storage, 'return', clc.user, item, clc.library, clc)
        # The event will be logged in the clc

    def check_item(self, item=None, **kwargs):
        if not item:
            raise Exception('There needs to be an item')
        if isinstance(item, (list, tuple)):
            raise Exception('Only one item can be returned.')
        if not isinstance(item, CirculationItem):
            raise Exception('The item must be of the type CirculationItem.')
        if item.current_status != 'on_loan':
            raise Exception('The item must on loan to be returned.')


class ReturnMissingConfig(ConfigBase):
    new_status = 'on_shelf'
    parameters = ['item']

    # @log_event('return_missing', ['item'])
    def run(self, _storage, item=None, **kwargs):
        create_event(_storage, 'return_missing', None, item, None, None)

    def check_item(self, item=None, **kwargs):
        if not item:
            raise Exception('There needs to be an item')
        if isinstance(item, (list, tuple)):
            raise Exception('Only one item can be returned from missing.')
        if not isinstance(item, CirculationItem):
            raise Exception('The item must be of the type CirculationItem.')
        if item.current_status != 'missing':
            raise Exception('The item must be missing to be returned')


item_config = {
    "on_shelf":
        {
            "loan": LoanConfig,
            "lose_from_shelf": LoseConfig,
            "request": RequestConfig
        },
    "on_loan":
        {
            "return": ReturnConfig,
            "lose_from_loan": LoseConfig,
            "request": RequestConfig
        },
    "missing":
        {
            "return": ReturnMissingConfig
        }
}
