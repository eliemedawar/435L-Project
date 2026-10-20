"""Asset validation and database operations. Developed by: Marc Bteich."""
from ipaddress import ip_address

from sqlalchemy import func

from common.clients import fetch_service, log_event
from common.db import db
from common.enums import ASSET_STATUSES, SEVERITIES
from common.errors import APIError, NotFoundError, ValidationError
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.assets import ASSET_TYPES, Asset


class UsersUnavailable(APIError):
    status_code = 503


class AssetValidator:
    CREATE_FIELDS = ("asset_name", "asset_type", "ip_address", "operating_system",
                     "owner_id", "department", "location", "criticality", "status")
    UPDATE_FIELDS = ("asset_name", "owner_id", "department", "criticality", "status")
    SEARCH_FIELDS = ("name", "type", "ip", "department", "criticality")

    @staticmethod
    def ip(value):
        if not isinstance(value, str) or "%" in value:
            raise ValidationError("'ip_address' must be an IPv4 or IPv6 address")
        try:
            return str(ip_address(value.strip()))
        except ValueError:
            raise ValidationError("'ip_address' must be an IPv4 or IPv6 address")

    @classmethod
    def validate(cls, data, update=False):
        reject_unknown_fields(data, cls.UPDATE_FIELDS if update else cls.CREATE_FIELDS)
        if not update:
            require_fields(data, ("asset_name", "asset_type", "ip_address", "owner_id", "department", "criticality"))
        result = {}
        for field, length in (("asset_name", 150), ("department", 100),
                              ("operating_system", 100), ("location", 150)):
            if field in data:
                result[field] = clean_string(data, field, length, required=field in ("asset_name", "department"))
        for field, allowed in (("asset_type", ASSET_TYPES), ("criticality", SEVERITIES), ("status", ASSET_STATUSES)):
            if field in data:
                result[field] = validate_enum(data[field], allowed, field)
        if "ip_address" in data:
            result["ip_address"] = cls.ip(data["ip_address"])
        if "owner_id" in data:
            value = data["owner_id"]
            if type(value) is not int or not 1 <= value <= 9223372036854775807:
                raise ValidationError("'owner_id' must be a positive 64-bit integer")
            result["owner_id"] = value
        if not update:
            result.setdefault("status", "Active")
        return result


class AssetService:
    @staticmethod
    def get(asset_id):
        if not 1 <= asset_id <= 9223372036854775807:
            raise NotFoundError(f"Asset with id {asset_id} not found")
        asset = db.session.get(Asset, asset_id)
        if asset is None:
            raise NotFoundError(f"Asset with id {asset_id} not found")
        return asset

    @staticmethod
    def verify_owner(owner_id):
        status, owner = fetch_service("users", f"/internal/users/{owner_id}")
        if status == 404:
            raise ValidationError(f"User with id {owner_id} does not exist")
        if status != 200 or not isinstance(owner, dict):
            raise UsersUnavailable("Users Service is unavailable; cannot verify the asset owner")

    @classmethod
    def create(cls, data, actor):
        values = AssetValidator.validate(data)
        cls.verify_owner(values["owner_id"])
        asset = Asset(**values)
        db.session.add(asset)
        db.session.commit()
        log_event(actor["user_id"], "ASSET_CREATED", f"Created asset {asset.id}", service="assets")
        return asset

    @classmethod
    def update(cls, asset_id, data, actor):
        values = AssetValidator.validate(data, update=True)
        asset = cls.get(asset_id)
        if "owner_id" in values:
            cls.verify_owner(values["owner_id"])
        for field, value in values.items():
            setattr(asset, field, value)
        db.session.commit()
        log_event(actor["user_id"], "ASSET_UPDATED",
                  f"Updated asset {asset.id}: {', '.join(sorted(values))}", service="assets")
        return asset

    @classmethod
    def delete(cls, asset_id, actor):
        asset = cls.get(asset_id)
        db.session.delete(asset)
        db.session.commit()  # Shared handler rolls back FK conflicts and returns 409.
        log_event(actor["user_id"], "ASSET_DELETED", f"Deleted asset {asset_id}", service="assets")

    @staticmethod
    def list_all():
        return Asset.query.order_by(Asset.id).all()

    @staticmethod
    def search(params):
        reject_unknown_fields(params, AssetValidator.SEARCH_FIELDS)
        if not params:
            raise ValidationError("Provide at least one search criterion")
        query = Asset.query
        for field in params:
            if len(params.getlist(field)) != 1:
                raise ValidationError(f"Provide '{field}' only once")
            value = clean_string(params, field, 150)
            if field == "name":
                query = query.filter(Asset.asset_name.icontains(value, autoescape=True))
            elif field == "department":
                query = query.filter(Asset.department.icontains(value, autoescape=True))
            elif field == "type":
                query = query.filter_by(asset_type=validate_enum(value, ASSET_TYPES, "type"))
            elif field == "ip":
                query = query.filter_by(ip_address=AssetValidator.ip(value))
            elif field == "criticality":
                query = query.filter_by(criticality=validate_enum(value, SEVERITIES, "criticality"))
        return query.order_by(Asset.id).all()

    @staticmethod
    def stats():
        counts = dict(db.session.query(Asset.asset_type, func.count(Asset.id)).group_by(Asset.asset_type).all())
        return {
            "total_assets": Asset.query.count(),
            "critical_assets": Asset.query.filter_by(criticality="Critical").count(),
            "by_type": {kind: counts.get(kind, 0) for kind in ASSET_TYPES},
        }
