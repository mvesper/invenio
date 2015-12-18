from invenio.ext.sqlalchemy import db

from invenio.modules.circulation.models import CirculationObject, ArrayType


class IllLoanCycle(CirculationObject, db.Model):
    __tablename__ = 'ill_loan_cycle'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    current_status = db.Column(db.String(255))
    additional_statuses = db.Column(ArrayType(255))
    item_id = db.Column(db.BigInteger,
                        db.ForeignKey('circulation_item.id'))
    item = db.relationship('CirculationItem')
    user_id = db.Column(db.BigInteger,
                        db.ForeignKey('circulation_user.id'))
    user = db.relationship('CirculationUser')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    delivery = db.Column(db.String(255))
    comments = db.Column(db.String(255))
    issued_date = db.Column(db.DateTime)
    creation_date = db.Column(db.DateTime)
    modification_date = db.Column(db.DateTime)
    _data = db.Column(db.LargeBinary)

    STATUS_REQUESTED = 'requested'
    STATUS_ORDERED = 'ordered'
    STATUS_DECLINED = 'declined'
    STATUS_CANCELED = 'canceled'
    STATUS_ON_LOAN = 'on_loan'
    STATUS_FINISHED = 'finished'
    STATUS_SEND_BACK = 'send_back'

    EVENT_ILL_CLC_REQUEST = 'ill_clc_requested'
    EVENT_ILL_CLC_ORDERED = 'ill_clc_ordered'
    EVENT_ILL_CLC_DECLINED = 'ill_clc_declined'
    EVENT_ILL_CLC_CANCELED= 'ill_clc_canceled'
    EVENT_ILL_CLC_DELIVERED = 'ill_clc_delivered'
    EVENT_ILL_CLC_EXTENSION_REQUESTED = 'ill_clc_extension_requested'
    EVENT_ILL_CLC_FINISHED = 'ill_clc_FINISHED'
    EVENT_ILL_CLC_SEND_BACK = 'ill_clc_send_back'

    DELIVERY_DEFAULT = 'pick_up'


entities = [('Ill Loan Cycle', 'ill_loan_cycle', IllLoanCycle)]
