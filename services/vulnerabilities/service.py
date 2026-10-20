"""Validation and remediation lifecycle. Developed by: Marc Bteich."""
import math
import re
from sqlalchemy import func
from common.clients import fetch_service, get_service, log_event, send_notification
from common.db import db, utcnow
from common.enums import SEVERITIES, VULNERABILITY_FLOW, next_status
from common.errors import APIError, NotFoundError, ValidationError
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.vulnerabilities import Vulnerability


class VulnerabilityValidator:
    CREATE = ('title','description','cve_id','cvss_score','severity','asset_id','discovery_source')
    UPDATE = ('description','severity','status','cvss_score')
    SEARCH = ('cve','severity','asset','status')

    @staticmethod
    def cve(value):
        if not isinstance(value, str) or len(value) > 40 or not re.fullmatch(r'CVE-[0-9]{4}-[0-9]{4,}', value):
            raise ValidationError('CVE must match CVE-YYYY-NNNN or a longer numeric suffix')
        return value

    @staticmethod
    def score(value):
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 10:
            raise ValidationError('cvss_score must be a finite number from 0.0 to 10.0')
        if abs(value * 10 - round(value * 10)) > 1e-8:
            raise ValidationError('cvss_score supports at most one decimal place')
        return value

    @classmethod
    def validate(cls, data, update=False):
        reject_unknown_fields(data, cls.UPDATE if update else cls.CREATE)
        if not update:
            require_fields(data, cls.CREATE)
        values = {}
        for field, limit in (('title',150),('description',2000),('discovery_source',150)):
            if field in data:
                values[field] = clean_string(data, field, limit)
        if 'cve_id' in data:
            values['cve_id'] = cls.cve(data['cve_id'])
        if 'cvss_score' in data:
            values['cvss_score'] = cls.score(data['cvss_score'])
        if 'severity' in data:
            values['severity'] = validate_enum(data['severity'], SEVERITIES, 'severity')
        if 'status' in data:
            values['status'] = validate_enum(data['status'], VULNERABILITY_FLOW, 'status')
        if 'asset_id' in data:
            value = data['asset_id']
            if type(value) is not int or not 0 < value < 2**63:
                raise ValidationError('asset_id must be a positive 64-bit integer')
            values['asset_id'] = value
        return values


class VulnerabilityService:
    @staticmethod
    def get(record_id):
        item = db.session.get(Vulnerability, record_id) if 0 < record_id < 2**63 else None
        if item is None:
            raise NotFoundError(f'Vulnerability {record_id} not found')
        return item

    @staticmethod
    def create(data, actor):
        values = VulnerabilityValidator.validate(data)
        status, _ = fetch_service('assets', f"/internal/assets/{values['asset_id']}")
        if status == 404:
            raise ValidationError('Affected asset does not exist')
        if status != 200:
            raise APIError('Cannot verify affected asset: Assets Service unavailable', 503)
        admins = []
        if values['severity'] == 'Critical':
            admins = get_service('users','/internal/users',params={'role':'admin'})
            if admins is None:
                raise APIError('Cannot identify administrator notification recipients',503)
        item = Vulnerability(**values)
        db.session.add(item)
        db.session.commit()
        log_event(actor['user_id'],'VULNERABILITY_CREATED',f'Created vulnerability {item.id}',service='vulnerabilities')
        for admin in admins:
            send_notification(admin['id'],f'Critical vulnerability #{item.id}',item.title,'Vulnerability Alert','Critical')
        return item

    @classmethod
    def update(cls, record_id, data, actor):
        values = VulnerabilityValidator.validate(data, update=True)
        item = cls.get(record_id)
        previous = item.status
        if 'status' in values:
            if values['status'] != next_status(VULNERABILITY_FLOW, item.status):
                raise ValidationError(f'Invalid transition from {item.status}; next status is {next_status(VULNERABILITY_FLOW,item.status)}')
            if values['status'] == 'Resolved':
                item.resolution_date = utcnow()
        for key,value in values.items():
            setattr(item,key,value)
        db.session.commit()
        log_event(actor['user_id'],'VULNERABILITY_UPDATED',
                  f'Updated vulnerability {item.id}: {previous} -> {item.status}',service='vulnerabilities')
        return item

    @classmethod
    def delete(cls, record_id, actor):
        db.session.delete(cls.get(record_id))
        db.session.commit()
        log_event(actor['user_id'],'VULNERABILITY_DELETED',f'Deleted vulnerability {record_id}',service='vulnerabilities')

    @staticmethod
    def list_all():
        return Vulnerability.query.order_by(Vulnerability.id).all()

    @staticmethod
    def search(params):
        reject_unknown_fields(params,VulnerabilityValidator.SEARCH)
        if not params:
            raise ValidationError('Provide at least one search criterion')
        query=Vulnerability.query
        for key in params:
            if len(params.getlist(key)) != 1:
                raise ValidationError(f'Provide {key} only once')
            value=clean_string(params,key,150)
            if key=='cve':
                query=query.filter_by(cve_id=VulnerabilityValidator.cve(value))
            elif key=='asset':
                if not value.isascii() or not value.isdigit() or not 0 < int(value) < 2**63:
                    raise ValidationError('asset must be a positive 64-bit integer')
                query=query.filter_by(asset_id=int(value))
            elif key=='severity':
                query=query.filter_by(severity=validate_enum(value,SEVERITIES,'severity'))
            elif key=='status':
                query=query.filter_by(status=validate_enum(value,VULNERABILITY_FLOW,'status'))
        return query.order_by(Vulnerability.id).all()

    @staticmethod
    def stats():
        def grouped(column,keys):
            counts=dict(db.session.query(column,func.count(Vulnerability.id)).group_by(column).all())
            return {key:counts.get(key,0) for key in keys}
        return dict(total_vulnerabilities=Vulnerability.query.count(),
                    critical_vulnerabilities=Vulnerability.query.filter_by(severity='Critical').count(),
                    by_severity=grouped(Vulnerability.severity,SEVERITIES),
                    by_status=grouped(Vulnerability.status,VULNERABILITY_FLOW))
