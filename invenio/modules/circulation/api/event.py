from invenio.modules.circulation.models import CirculationEvent


def create(user=None, item=None, loan_cycle=None, location=None,
           mail_template=None, loan_rule=None, event=None, description=None):
    CirculationEvent.new(user=user, item=item, loan_cycle=loan_cycle,
                         location=location, mail_template=mail_template,
                         loan_rule=loan_rule,
                         event=event, description=description)


def update(ce, **kwargs):
    raise Exception('Events are not supposed to be changed.')


def delete(ce):
    raise Exception('Events are not supposed to be deleted.')


schema = {}
