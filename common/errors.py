"""Uniform success/error responses and error handlers for every service.

Success: {"status": "success", "message": "...", "data": {...}}
Error:   {"status": "error",   "message": "..."}
"""
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from common.db import db


class APIError(Exception):
    """Base class: raise one of the subclasses anywhere and the handler turns it into JSON."""
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(APIError):
    status_code = 400


class AuthError(APIError):
    status_code = 401


class ForbiddenError(APIError):
    status_code = 403


class NotFoundError(APIError):
    status_code = 404


class ConflictError(APIError):
    status_code = 409


def success(data=None, message="OK", status_code=200):
    return jsonify({"status": "success", "message": message, "data": data}), status_code


def error_response(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code


# Friendlier messages for errors raised by Flask itself (unknown URL, wrong method, ...)
_HTTP_MESSAGES = {
    400: "Bad request",
    404: "Resource not found",
    405: "HTTP method not allowed on this endpoint",
    415: "Content-Type must be application/json",
}


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err):
        db.session.rollback()
        return error_response(err.message, err.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return error_response(_HTTP_MESSAGES.get(err.code, err.description), err.code)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        db.session.rollback()
        app.logger.warning("Integrity error: %s", err.orig)
        return error_response("Operation violates a database constraint (duplicate or linked record)", 409)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        app.logger.exception("Unhandled error")
        return error_response("Internal server error", 500)
