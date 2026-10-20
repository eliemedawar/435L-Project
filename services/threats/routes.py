"""Threat routes. Developed by: Marc Bteich."""
from flask import Blueprint, g, request
from common.auth import require_auth, require_service
from common.errors import success
from common.validators import get_json_body
from services.threats.service import ThreatService

threats_bp = Blueprint('threats', __name__)


# Developed by: Marc Bteich
@threats_bp.route('/threats', methods=['POST'])
@require_auth(roles=['admin'])
def create():
    return success(ThreatService.create(get_json_body(), g.user).to_dict(), 'Threat created', 201)


# Developed by: Marc Bteich
@threats_bp.route('/threats', methods=['GET'])
@require_auth(roles=['admin', 'analyst', 'auditor'])
def list_all():
    items = ThreatService.list_all()
    return success({'count': len(items), 'threats': [i.to_dict() for i in items]})


# Developed by: Marc Bteich
@threats_bp.route('/threats/<int:record_id>', methods=['GET'])
@require_auth(roles=['admin', 'analyst', 'auditor'])
def get(record_id):
    return success(ThreatService.get(record_id).to_dict())


# Developed by: Marc Bteich
@threats_bp.route('/threats/search', methods=['GET'])
@require_auth(roles=['admin', 'analyst'])
def search():
    items = ThreatService.search(request.args)
    return success({'count': len(items), 'threats': [i.to_dict() for i in items]})


# Developed by: Marc Bteich
@threats_bp.route('/threats/<int:record_id>', methods=['PUT'])
@require_auth(roles=['admin'])
def update(record_id):
    return success(ThreatService.update(record_id, get_json_body(), g.user).to_dict(), 'Threat updated')


# Developed by: Marc Bteich
@threats_bp.route('/threats/<int:record_id>', methods=['DELETE'])
@require_auth(roles=['admin'])
def delete(record_id):
    ThreatService.delete(record_id, g.user)
    return success(None, 'Threat deleted')


# Developed by: Marc Bteich
@threats_bp.route('/internal/stats', methods=['GET'])
@require_service
def stats():
    return success(ThreatService.stats())
