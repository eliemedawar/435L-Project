"""HTTP-based asset, threat and vulnerability reports. Developed by: Marc Bteich."""
from flask import Blueprint
from common.auth import require_auth
from common.errors import success
from services.reports.routes_a import ReportBuilder

reports_b_bp=Blueprint('reports_b',__name__)


# Developed by: Marc Bteich
@reports_b_bp.route('/reports/assets',methods=['GET'])
@require_auth(roles=['admin','auditor'])
def assets():
    builder=ReportBuilder('asset')
    stats=builder.collect('assets',required=True)
    return success(builder.build(dict(total_assets=stats['total_assets'],critical_assets=stats['critical_assets'],
                                     assets_by_type=stats['by_type'])),'Asset report generated')


# Developed by: Marc Bteich
@reports_b_bp.route('/reports/threats',methods=['GET'])
@require_auth(roles=['admin','auditor'])
def threats():
    builder=ReportBuilder('threat')
    stats=builder.collect('threats',required=True)
    return success(builder.build(dict(total_threats=stats['total_threats'],threats_by_severity=stats['by_severity'],
                                     threats_by_type=stats['by_type'],recently_added=stats['recently_added'])),'Threat report generated')


# Developed by: Marc Bteich
@reports_b_bp.route('/reports/vulnerabilities',methods=['GET'])
@require_auth(roles=['admin','auditor'])
def vulnerabilities():
    builder=ReportBuilder('vulnerability')
    stats=builder.collect('vulnerabilities',required=True)
    return success(builder.build(dict(total_vulnerabilities=stats['total_vulnerabilities'],
        critical_vulnerabilities=stats['critical_vulnerabilities'],vulnerabilities_by_severity=stats['by_severity'],
        vulnerabilities_by_status=stats['by_status'])),'Vulnerability report generated')
