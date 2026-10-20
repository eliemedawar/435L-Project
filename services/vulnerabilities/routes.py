"""Vulnerability routes. Developed by: Marc Bteich."""
from flask import Blueprint, g, request
from common.auth import require_auth, require_service
from common.errors import success
from common.validators import get_json_body
from services.vulnerabilities.service import VulnerabilityService

vulnerabilities_bp = Blueprint('vulnerabilities', __name__)


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities', methods=['POST'])
@require_auth(roles=['admin'])
def create():
    return success(VulnerabilityService.create(get_json_body(),g.user).to_dict(),'Vulnerability created',201)


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities', methods=['GET'])
@require_auth(roles=['admin','analyst','auditor'])
def list_all():
    items=VulnerabilityService.list_all()
    return success({'count':len(items),'vulnerabilities':[i.to_dict() for i in items]})


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities/<int:record_id>', methods=['GET'])
@require_auth(roles=['admin','analyst','auditor'])
def get(record_id):
    return success(VulnerabilityService.get(record_id).to_dict())


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities/<int:record_id>', methods=['PUT'])
@require_auth(roles=['admin','analyst'])
def update(record_id):
    return success(VulnerabilityService.update(record_id,get_json_body(),g.user).to_dict(),'Vulnerability updated')


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities/search', methods=['GET'])
@require_auth(roles=['admin','analyst','auditor'])
def search():
    items=VulnerabilityService.search(request.args)
    return success({'count':len(items),'vulnerabilities':[i.to_dict() for i in items]})


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/vulnerabilities/<int:record_id>', methods=['DELETE'])
@require_auth(roles=['admin'])
def delete(record_id):
    VulnerabilityService.delete(record_id,g.user)
    return success(None,'Vulnerability deleted')


# Developed by: Marc Bteich
@vulnerabilities_bp.route('/internal/stats', methods=['GET'])
@require_service
def stats():
    return success(VulnerabilityService.stats())
