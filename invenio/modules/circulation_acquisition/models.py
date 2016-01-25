from invenio.ext.sqlalchemy import db

from invenio.modules.circulation.models import CirculationObject, ArrayType


class AcquisitionLoanCycle(CirculationObject, db.Model):
    __tablename__ = 'acquisition_loan_cycle'
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
    desired_end_date = db.Column(db.Date)
    delivery = db.Column(db.String(255))
    comments = db.Column(db.String(255))
    issued_date = db.Column(db.DateTime)
    creation_date = db.Column(db.DateTime)
    modification_date = db.Column(db.DateTime)
    _data = db.Column(db.LargeBinary)

    STATUS_REQUESTED = 'requested'
    STATUS_ORDERED = 'ordered'
    STATUS_RECEIVED = 'received'
    STATUS_DELIVERED = 'delivered'
    STATUS_DECLINED = 'declined'
    STATUS_CANCELED = 'canceled'

    TYPE_ACQUISITION = 'acquisition'
    TYPE_PURCHASE = 'purchase'

    EVENT_ACQUISITION_REQUEST = 'acquisition_requested'
    EVENT_PURCHASE_REQUEST = 'purchase_requested'
    EVENT_ACQUISITION_ORDERED = 'acquisition_ordered'
    EVENT_ACQUISITION_RECEIVED = 'acquisition_received'
    EVENT_ACQUISITION_DELIVERED = 'acquisition_delivered'
    EVENT_ACQUISITION_CANCELED = 'acquisition_canceled'
    EVENT_ACQUISITION_DECLINED = 'acquisition_declined'

    DELIVERY_DEFAULT = 'pick_up'

    _json_schema = {'type': 'object',
                    'title': 'Loan Cycle',
                    'properties': {
                        'id': {'type': 'integer'},
                        'item_id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'group_uuid': {'type': 'string'},
                        'current_status': {'type': 'string'},
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                        'issued_date': {'type': 'string'},
                        'requested_extension_end_date': {'type': 'string'},
                        }
                    }


entities = [('Acquisition Loan Cycle', 'acquisition_loan_cycle',
             AcquisitionLoanCycle)]
