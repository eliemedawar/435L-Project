"""Response workflow and durable execution history. Developed by: Marc Bteich."""
from common.clients import fetch_service, log_event
from common.db import db, iso, utcnow
from common.enums import ACTION_STATUSES, INCIDENT_CATEGORIES, SEVERITIES, next_status
from common.errors import APIError, ConflictError, NotFoundError, ValidationError
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.playbooks import Playbook, ResponseAction


class PlaybookValidator:
    @staticmethod
    def positive(value, field):
        if type(value) is not int or not 0 < value < 2**63:
            raise ValidationError(f'{field} must be a positive 64-bit integer')
        return value

    @staticmethod
    def user(user_id):
        PlaybookValidator.positive(user_id,'assigned_user_id')
        status,user=fetch_service('users',f'/internal/users/{user_id}')
        if status==404:
            raise ValidationError('Assigned user does not exist')
        if status!=200 or not user:
            raise APIError('Cannot verify assigned user: Users Service unavailable',503)
        if user['account_status']!='Active':
            raise ValidationError('Assigned user must be Active')
        return user_id


class PlaybookService:
    @staticmethod
    def get(record_id):
        item=db.session.get(Playbook,record_id) if 0 < record_id < 2**63 else None
        if item is None:
            raise NotFoundError(f'Playbook {record_id} not found')
        return item

    @staticmethod
    def action(record_id):
        item=db.session.get(ResponseAction,record_id) if 0 < record_id < 2**63 else None
        if item is None:
            raise NotFoundError(f'Response action {record_id} not found')
        return item

    @staticmethod
    def history(action, actor, previous=None):
        # Assign a new list so SQLAlchemy detects JSON changes; save atomically
        # with the action. Clients cannot supply or replace this history.
        action.execution_history=list(action.execution_history or [])+[dict(
            actor_id=actor['user_id'],at=iso(utcnow()),from_status=previous,to_status=action.status,
            assigned_user_id=action.assigned_user_id,completion_date=iso(action.completion_date))]

    @staticmethod
    def create(data,actor):
        fields=('name','description','incident_category','severity')
        reject_unknown_fields(data,fields)
        require_fields(data,fields)
        item=Playbook(name=clean_string(data,'name',150),description=clean_string(data,'description',2000),
                      incident_category=validate_enum(data['incident_category'],INCIDENT_CATEGORIES,'incident_category'),
                      severity=validate_enum(data['severity'],SEVERITIES,'severity'),created_by=actor['user_id'])
        db.session.add(item)
        db.session.commit()
        log_event(actor['user_id'],'PLAYBOOK_CREATED',f'Created playbook {item.id}',service='playbooks')
        return item

    @classmethod
    def add_action(cls,record_id,data,actor):
        reject_unknown_fields(data,('description','step_number','assigned_user_id'))
        require_fields(data,('description','step_number'))
        cls.get(record_id)
        number=PlaybookValidator.positive(data['step_number'],'step_number')
        if ResponseAction.query.filter_by(playbook_id=record_id,step_number=number).first():
            raise ConflictError('Step number already exists in this playbook')
        assigned=PlaybookValidator.user(data['assigned_user_id']) if 'assigned_user_id' in data else None
        item=ResponseAction(playbook_id=record_id,description=clean_string(data,'description',2000),
                            step_number=number,status='Pending',assigned_user_id=assigned)
        cls.history(item,actor)
        db.session.add(item)
        db.session.commit()
        log_event(actor['user_id'],'ACTION_CREATED',f'Created action {item.id} in playbook {record_id}, step {number}',service='playbooks')
        return item

    @classmethod
    def update_action(cls,record_id,data,actor):
        reject_unknown_fields(data,('status','assigned_user_id'))
        item=cls.action(record_id)
        previous=item.status
        if item.status=='Completed':
            raise ValidationError('Completed action cannot change')
        new_status=data.get('status',item.status)
        if 'status' in data:
            validate_enum(new_status,ACTION_STATUSES,'status')
            if new_status!=next_status(ACTION_STATUSES,item.status):
                raise ValidationError(f'Invalid action transition: {item.status} -> {new_status}')
        assigned=PlaybookValidator.user(data['assigned_user_id']) if 'assigned_user_id' in data else item.assigned_user_id
        if new_status in ('In Progress','Completed') and assigned is None:
            raise ValidationError('Assign a user before executing an action')
        item.status,item.assigned_user_id=new_status,assigned
        if new_status=='Completed':
            item.completion_date=utcnow()
        cls.history(item,actor,previous)
        db.session.commit()
        log_event(actor['user_id'],'ACTION_UPDATED',
                  f'Action {item.id} playbook {item.playbook_id}: {previous} -> {item.status}, assigned {assigned}, completed {iso(item.completion_date)}',service='playbooks')
        return item

    @classmethod
    def delete(cls,record_id,actor):
        item=cls.get(record_id)
        db.session.delete(item)
        db.session.commit()
        log_event(actor['user_id'],'PLAYBOOK_DELETED',f'Deleted playbook {record_id} and its actions',service='playbooks')

    @staticmethod
    def list_all():
        return Playbook.query.order_by(Playbook.id).all()
