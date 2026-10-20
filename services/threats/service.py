"""Indicator validation and business rules. Developed by: Marc Bteich."""
import re
from ipaddress import ip_address
from sqlalchemy import func
from common.clients import get_service, log_event, send_notification
from common.db import db
from common.enums import SEVERITIES, THREAT_TYPES
from common.errors import APIError, ConflictError, NotFoundError, ValidationError
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.threats import Threat


class ThreatValidator:
    FIELDS = ('threat_type', 'threat_value', 'description', 'severity', 'source')
    UPDATE = ('description', 'severity', 'source')
    SEARCH = ('type', 'value', 'severity', 'source')

    @staticmethod
    def value(kind, value):
        value = clean_string({'value': value}, 'value', 255)
        if kind == 'IP Address':
            try:
                if '%' in value:
                    raise ValueError()
                return str(ip_address(value))
            except ValueError:
                raise ValidationError('Invalid IP threat value')
        if kind == 'Domain':
            value = value.rstrip('.').lower()
            if len(value) > 253 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?', value):
                raise ValidationError('Invalid domain threat value')
        if kind == 'File Hash':
            if not re.fullmatch(r'(?:[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})', value):
                raise ValidationError('File Hash must be MD5, SHA1 or SHA256 hexadecimal')
            value = value.lower()
        return value

    @classmethod
    def validate(cls, data, update=False):
        reject_unknown_fields(data, cls.UPDATE if update else cls.FIELDS)
        if not update:
            require_fields(data, cls.FIELDS)
        result = {}
        if not update:
            result['threat_type'] = validate_enum(data['threat_type'], THREAT_TYPES, 'threat_type')
            result['threat_value'] = cls.value(result['threat_type'], data['threat_value'])
        for field, limit in (('description', 2000), ('source', 150)):
            if field in data:
                result[field] = clean_string(data, field, limit)
        if 'severity' in data:
            result['severity'] = validate_enum(data['severity'], SEVERITIES, 'severity')
        return result


class ThreatService:
    @staticmethod
    def get(record_id):
        item = db.session.get(Threat, record_id) if 0 < record_id < 2**63 else None
        if item is None:
            raise NotFoundError(f'Threat {record_id} not found')
        return item

    @staticmethod
    def create(data, actor):
        values = ThreatValidator.validate(data)
        if Threat.query.filter_by(threat_type=values['threat_type'], threat_value=values['threat_value']).first():
            raise ConflictError('Threat type/value pair already exists')
        admins = []
        if values['severity'] == 'Critical':
            admins = get_service('users', '/internal/users', params={'role': 'admin'})
            if admins is None:
                raise APIError('Cannot identify administrator notification recipients', 503)
        item = Threat(**values)
        db.session.add(item)
        db.session.commit()
        log_event(actor['user_id'], 'THREAT_CREATED', f'Created threat {item.id}', service='threats')
        for admin in admins:
            send_notification(admin['id'], f'Critical threat #{item.id}', item.threat_value, 'Threat Alert', 'Critical')
        return item

    @classmethod
    def update(cls, record_id, data, actor):
        values = ThreatValidator.validate(data, update=True)
        item = cls.get(record_id)
        for key, value in values.items():
            setattr(item, key, value)
        db.session.commit()
        log_event(actor['user_id'], 'THREAT_UPDATED', f'Updated threat {item.id}', service='threats')
        return item

    @classmethod
    def delete(cls, record_id, actor):
        db.session.delete(cls.get(record_id))
        db.session.commit()
        log_event(actor['user_id'], 'THREAT_DELETED', f'Deleted threat {record_id}', service='threats')

    @staticmethod
    def list_all():
        return Threat.query.order_by(Threat.id).all()

    @staticmethod
    def search(params):
        reject_unknown_fields(params, ThreatValidator.SEARCH)
        if not params:
            raise ValidationError('Provide at least one search criterion')
        query = Threat.query
        for key in params:
            if len(params.getlist(key)) != 1:
                raise ValidationError(f'Provide {key} only once')
            value = clean_string(params, key, 255)
            if key == 'type':
                query = query.filter_by(threat_type=validate_enum(value, THREAT_TYPES, 'type'))
            elif key == 'severity':
                query = query.filter_by(severity=validate_enum(value, SEVERITIES, 'severity'))
            else:
                column = Threat.threat_value if key == 'value' else Threat.source
                query = query.filter(column.icontains(value, autoescape=True))
        return query.order_by(Threat.id).all()

    @staticmethod
    def stats():
        def grouped(column, keys):
            counts = dict(db.session.query(column, func.count(Threat.id)).group_by(column).all())
            return {key: counts.get(key, 0) for key in keys}
        return dict(total_threats=Threat.query.count(), by_severity=grouped(Threat.severity, SEVERITIES),
                    by_type=grouped(Threat.threat_type, THREAT_TYPES),
                    recently_added=[t.to_dict() for t in Threat.query.order_by(Threat.date_added.desc(), Threat.id.desc()).limit(5)])
