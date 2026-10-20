"""Playbook routes. Developed by: Marc Bteich."""
from flask import Blueprint,g
from common.auth import require_auth
from common.errors import success
from common.validators import get_json_body
from services.playbooks.service import PlaybookService

playbooks_bp=Blueprint('playbooks',__name__)


# Developed by: Marc Bteich
@playbooks_bp.route('/playbooks',methods=['POST'])
@require_auth(roles=['admin'])
def create():
    return success(PlaybookService.create(get_json_body(),g.user).to_dict(),'Playbook created',201)


# Developed by: Marc Bteich
@playbooks_bp.route('/playbooks',methods=['GET'])
@require_auth(roles=['admin','analyst','auditor'])
def list_all():
    items=PlaybookService.list_all()
    return success({'count':len(items),'playbooks':[i.to_dict() for i in items]})


# Developed by: Marc Bteich
@playbooks_bp.route('/playbooks/<int:record_id>',methods=['GET'])
@require_auth(roles=['admin','analyst','auditor'])
def get(record_id):
    return success(PlaybookService.get(record_id).to_dict(include_actions=True))


# Developed by: Marc Bteich
@playbooks_bp.route('/playbooks/<int:record_id>/actions',methods=['POST'])
@require_auth(roles=['admin','analyst'])
def add_action(record_id):
    return success(PlaybookService.add_action(record_id,get_json_body(),g.user).to_dict(),'Action created',201)


# Developed by: Marc Bteich
@playbooks_bp.route('/actions/<int:record_id>/status',methods=['PUT'])
@require_auth(roles=['admin','analyst'])
def update_action(record_id):
    return success(PlaybookService.update_action(record_id,get_json_body(),g.user).to_dict(),'Action updated')


# Developed by: Marc Bteich
@playbooks_bp.route('/playbooks/<int:record_id>',methods=['DELETE'])
@require_auth(roles=['admin'])
def delete(record_id):
    PlaybookService.delete(record_id,g.user)
    return success(None,'Playbook deleted')
