"""Assets HTTP endpoints. Developed by: Marc Bteich."""
from flask import Blueprint, g, request

from common.auth import require_auth, require_service
from common.errors import success
from common.roles import ADMIN, ANALYST, AUDITOR
from common.validators import get_json_body, reject_unknown_fields
from services.assets.service import AssetService

assets_bp = Blueprint("assets", __name__)


# Developed by: Marc Bteich
@assets_bp.route("/assets", methods=["POST"])
@require_auth(roles=[ADMIN])
def create_asset():
    asset = AssetService.create(get_json_body(), g.user)
    return success(asset.to_dict(), "Asset created successfully", 201)


# Developed by: Marc Bteich
@assets_bp.route("/assets/<int:asset_id>", methods=["PUT"])
@require_auth(roles=[ADMIN])
def update_asset(asset_id):
    asset = AssetService.update(asset_id, get_json_body(), g.user)
    return success(asset.to_dict(), "Asset updated successfully")


# Developed by: Marc Bteich
@assets_bp.route("/assets/<int:asset_id>", methods=["DELETE"])
@require_auth(roles=[ADMIN])
def delete_asset(asset_id):
    AssetService.delete(asset_id, g.user)
    return success(None, f"Asset {asset_id} deleted successfully")


# Developed by: Marc Bteich
@assets_bp.route("/assets", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def list_assets():
    reject_unknown_fields(request.args, ())
    assets = AssetService.list_all()
    return success({"count": len(assets), "assets": [a.to_dict() for a in assets]}, "Assets retrieved successfully")


# Developed by: Marc Bteich
@assets_bp.route("/assets/<int:asset_id>", methods=["GET"])
@require_auth(roles=[ADMIN, ANALYST, AUDITOR])
def get_asset(asset_id):
    return success(AssetService.get(asset_id).to_dict(), "Asset retrieved successfully")


# Developed by: Marc Bteich
@assets_bp.route("/assets/search", methods=["GET"])
@require_auth(roles=[ADMIN, ANALYST, AUDITOR])
def search_assets():
    assets = AssetService.search(request.args)
    return success({"count": len(assets), "assets": [a.to_dict() for a in assets]}, "Asset search completed")


# Developed by: Marc Bteich
@assets_bp.route("/internal/stats", methods=["GET"])
@require_service
def internal_stats():
    return success(AssetService.stats())


# Developed by: Marc Bteich
@assets_bp.route("/internal/assets/<int:asset_id>", methods=["GET"])
@require_service
def internal_get_asset(asset_id):
    return success(AssetService.get(asset_id).to_dict())
