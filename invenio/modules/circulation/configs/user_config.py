from invenio.modules.circulation.configs.config_utils import ConfigBase
from invenio.modules.circulation.configs.config_utils import email_notification


class LoanConfig(ConfigBase):
    parameters = ['items', 'user', 'library', 'start_date', 'end_date']

    @email_notification('user_loan')
    def run(self, _storage,
            items=None, user=None, library=None,
            start_date=None, end_date=None,
            waitlist=False,
            **kwargs):

        for i, item in enumerate(items):
            item.run('loan', _storage=_storage,
                     item=item, user=user, library=library,
                     start_date=start_date, end_date=end_date,
                     waitlist=waitlist,
                     _notify=False)

    def check_all(self,
                  items=None, user=None, library=None,
                  start_date=None, end_date=None,
                  waitlist=False,
                  **kwargs):

        for item in items:
            item.validate_run('loan',
                              item=item, user=user, library=library,
                              start_date=start_date, end_date=end_date,
                              waitlist=waitlist,
                              _notify=False)


class RequestConfig(ConfigBase):
    parameters = ['items', 'user', 'library', 'start_date', 'end_date']

    @email_notification('user_request')
    def run(self, _storage,
            items=None, user=None, library=None,
            delivery='pick up', waitlist=False,
            start_date=None, end_date=None,
            **kwargs):

        for i, item in enumerate(items):
            item.run('request', _storage=_storage,
                     item=item, user=user, library=library,
                     start_date=start_date, end_date=end_date,
                     waitlist=waitlist,
                     _notify=False)

    def check_all(self,
                  items=None, user=None, library=None,
                  start_date=None, end_date=None,
                  waitlist=False, deliver='pick up',
                  **kwargs):

        for item in items:
            item.validate_run('loan',
                              item=item, user=user, library=library,
                              start_date=start_date, end_date=end_date,
                              waitlist=waitlist,
                              _notify=False)


class ReturnConfig(ConfigBase):
    parameters = ['items']

    def run(self, _storage,
            items=None, **kwargs):
        for item in items:
            item.run('return', _storage=_storage, item=item)

    def check_item(self, items=None, **kwargs):
        if not items:
            raise Exception('Items are required to loan an item')


user_config = {
    "active":
        {
            "loan": LoanConfig,
            "request": RequestConfig,
            "return": ReturnConfig
        }
}
