"""Flasgger/OpenAPI 3 configuration and automatic route documentation.

The small metadata catalogue below provides human-friendly descriptions. Route
discovery, path parameters, security, standard errors, and fallback operations
are generated from Flask's URL map, so a newly registered endpoint immediately
appears in the specification.
"""

from __future__ import annotations

import re
from copy import deepcopy

from flasgger import Swagger, swag_from


TAGS = [
    {"name": "System", "description": "Service health and availability."},
    {"name": "Authentication", "description": "Account and JWT operations."},
    {"name": "Documents", "description": "Secure legal-document management."},
    {"name": "AI", "description": "Classification, search, and NLP operations."},
    {"name": "Analytics", "description": "User-scoped dashboards and metrics."},
]

OPERATIONS = {
    "status.status": ("Get service status", "Checks the API and MongoDB connection.", "System"),
    "auth.register": ("Register an account", "Creates a user and returns a JWT access token.", "Authentication"),
    "auth.login": ("Sign in", "Authenticates an account and returns a JWT access token.", "Authentication"),
    "auth.forgot_password": ("Request password reset", "Emails a time-limited reset link when the account exists.", "Authentication"),
    "auth.reset_password": ("Reset password", "Replaces a password using a valid reset token.", "Authentication"),
    "auth.me": ("Get current user", "Returns the authenticated account.", "Authentication"),
    "auth.profile": ("Get profile", "Returns the authenticated professional profile.", "Authentication"),
    "auth.edit_profile": ("Update profile", "Updates supported professional profile fields.", "Authentication"),
    "protected.protected": ("Validate token", "Confirms that the supplied bearer token is valid.", "Authentication"),
    "documents.upload_document": ("Upload a document", "Uploads PDF/DOCX content and runs extraction, classification, keywords, and recommendations.", "Documents"),
    "documents.upload_document_legacy": ("Upload a document (legacy)", "Legacy alias for document upload.", "Documents"),
    "documents.list_documents": ("List documents", "Lists documents owned by the authenticated user.", "Documents"),
    "documents.get_document": ("Get document", "Returns one owned document and its metadata.", "Documents"),
    "documents.update_document": ("Update document metadata", "Updates governance and matter metadata.", "Documents"),
    "documents.get_document_text": ("Get extracted text", "Returns stored raw and cleaned document text.", "Documents"),
    "documents.view_original_document": ("View original document", "Streams the original PDF or DOCX file.", "Documents"),
    "documents.delete_document": ("Delete document", "Deletes an owned document and its stored file.", "Documents"),
    "documents.process_document_text": ("Extract document text", "Re-extracts and preprocesses text from the stored file.", "AI"),
    "documents.extract_document_keywords": ("Extract keywords", "Generates and stores ranked legal keywords.", "AI"),
    "documents.summarize_document": ("Summarize document", "Generates a TextRank summary with the requested length.", "AI"),
    "documents.process_document": ("Process document", "Runs keyword processing on extracted text.", "AI"),
    "documents.search_documents": ("Search documents", "Ranks owned documents by semantic TF-IDF similarity.", "AI"),
    "documents.recommend_similar_documents": ("Recommend documents", "Returns similar owned documents with optional category filtering.", "AI"),
    "classification.classify_legal_document": ("Classify legal text", "Predicts a legal category and confidence scores.", "AI"),
    "analytics.dashboard_analytics": ("Get dashboard analytics", "Returns user-scoped document, processing, and governance metrics.", "Analytics"),
}

PUBLIC_ENDPOINTS = {
    "status.status", "auth.register", "auth.login", "auth.forgot_password",
    "auth.reset_password", "classification.classify_legal_document",
}

JSON_BODIES = {
    "auth.register": ("RegistrationRequest", {"name": "Ada Counsel", "email": "ada@example.com", "password": "Secure123", "role": "user"}),
    "auth.login": ("LoginRequest", {"email": "ada@example.com", "password": "Secure123"}),
    "auth.forgot_password": ("ForgotPasswordRequest", {"email": "ada@example.com"}),
    "auth.reset_password": ("ResetPasswordRequest", {"token": "signed-reset-token", "password": "NewSecure123"}),
    "auth.edit_profile": ("ProfileUpdate", {"name": "Ada Counsel", "organization": "Example Chambers"}),
    "documents.update_document": ("DocumentUpdate", {"matter_name": "Example v Example", "review_status": "In review"}),
    "documents.search_documents": ("SearchRequest", {"query": "tenant eviction notice requirements"}),
    "documents.summarize_document": ("SummaryRequest", {"sentence_count": 5}),
    "classification.classify_legal_document": ("ClassificationRequest", {"text": "This employment agreement governs salary and termination."}),
}


SCHEMAS = {
    "Error": {
        "type": "object", "required": ["message"],
        "properties": {"message": {"type": "string", "example": "The request could not be completed."}, "status_code": {"type": "integer", "example": 400}},
    },
    "User": {
        "type": "object", "required": ["id", "name", "email", "role"],
        "properties": {
            "id": {"type": "string", "example": "665f1d5e1c9d440001abcdef"},
            "name": {"type": "string", "example": "Ada Counsel"},
            "email": {"type": "string", "format": "email", "example": "ada@example.com"},
            "role": {"type": "string", "enum": ["user", "admin"], "example": "user"},
            "organization": {"type": "string", "example": "Example Chambers"},
        },
    },
    "Document": {
        "type": "object", "required": ["id", "filename", "upload_date"],
        "properties": {
            "id": {"type": "string", "example": "665f1d5e1c9d440001abcdef"},
            "filename": {"type": "string", "example": "employment-agreement.pdf"},
            "upload_date": {"type": "string", "format": "date-time"},
            "predicted_category": {"type": "string", "example": "Employment"},
            "confidence_score": {"type": "number", "format": "float", "example": 0.92},
            "keywords": {"type": "array", "items": {"type": "string"}, "example": ["termination clause", "salary payment"]},
            "summary": {"type": "string", "example": "The agreement defines employment terms."},
        },
    },
    "RegistrationRequest": {"type": "object", "required": ["name", "email", "password"], "properties": {"name": {"type": "string"}, "email": {"type": "string", "format": "email"}, "password": {"type": "string", "format": "password", "minLength": 8}, "role": {"type": "string", "enum": ["user", "admin"]}, "admin_key": {"type": "string", "writeOnly": True}}},
    "LoginRequest": {"type": "object", "required": ["email", "password"], "properties": {"email": {"type": "string", "format": "email"}, "password": {"type": "string", "format": "password"}}},
    "ForgotPasswordRequest": {"type": "object", "required": ["email"], "properties": {"email": {"type": "string", "format": "email"}}},
    "ResetPasswordRequest": {"type": "object", "required": ["token", "password"], "properties": {"token": {"type": "string"}, "password": {"type": "string", "format": "password", "minLength": 8}}},
    "ProfileUpdate": {"type": "object", "properties": {"name": {"type": "string"}, "phone": {"type": "string"}, "organization": {"type": "string"}, "job_title": {"type": "string"}, "jurisdiction": {"type": "string"}, "professional_id": {"type": "string"}}},
    "DocumentUpdate": {"type": "object", "properties": {"matter_name": {"type": "string"}, "matter_number": {"type": "string"}, "client_name": {"type": "string"}, "review_status": {"type": "string", "enum": ["Needs review", "In review", "Approved", "Archived"]}, "confidentiality": {"type": "string"}, "privilege": {"type": "string"}, "notes": {"type": "string"}}},
    "SearchRequest": {"type": "object", "required": ["query"], "properties": {"query": {"type": "string", "minLength": 1}}},
    "SummaryRequest": {"type": "object", "properties": {"sentence_count": {"type": "integer", "minimum": 1, "maximum": 20, "default": 3}}},
    "ClassificationRequest": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string", "minLength": 1}}},
}


def _openapi_path(rule: str) -> str:
    return re.sub(r"<(?:[^:>]+:)?([^>]+)>", r"{\1}", rule)


def _response(description: str, example: dict | list | None = None):
    content = {"application/json": {"schema": {"type": "object"}}}
    if example is not None:
        content["application/json"]["example"] = example
    return {"description": description, "content": content}


def _operation(rule, endpoint: str, method: str) -> dict:
    summary, description, tag = OPERATIONS.get(
        endpoint,
        (endpoint.rsplit(".", 1)[-1].replace("_", " ").title(), "Automatically discovered Flask API operation.", "System"),
    )
    operation = {
        "summary": summary,
        "description": description,
        "tags": [tag],
        "operationId": f"{endpoint.replace('.', '_')}_{method.lower()}",
        "parameters": [
            {
                "name": argument, "in": "path", "required": True,
                "description": f"The {argument.replace('_', ' ')}.",
                "schema": {"type": "string"},
                "example": "665f1d5e1c9d440001abcdef",
            }
            for argument in sorted(rule.arguments)
        ],
        "responses": {
            "200": _response("Request completed successfully.", {"message": "Request completed successfully."}),
            "400": {"description": "Invalid request.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}, "example": {"message": "Invalid request."}}}},
            "500": {"description": "Unexpected server error.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}, "example": {"message": "An unexpected server error occurred.", "status_code": 500}}}},
        },
    }
    if endpoint not in PUBLIC_ENDPOINTS:
        operation["security"] = [{"bearerAuth": []}]
        operation["responses"]["401"] = {"description": "Missing or invalid JWT.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}, "example": {"message": "Authorization token is required.", "error": "token_missing"}}}}
    if rule.arguments:
        operation["responses"]["404"] = {"description": "Resource not found.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}, "example": {"message": "Document not found."}}}}
    if method == "POST" and endpoint in {"auth.register", "documents.upload_document", "documents.upload_document_legacy"}:
        operation["responses"]["201"] = _response("Resource created successfully.", {"message": "Resource created successfully."})
    if endpoint in JSON_BODIES:
        schema_name, example = JSON_BODIES[endpoint]
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}, "example": example}},
        }
    if endpoint in {"documents.upload_document", "documents.upload_document_legacy"}:
        operation["requestBody"] = {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "confidentiality": {"type": "string", "example": "Internal"},
                            "privilege": {"type": "string", "example": "Not privileged"},
                            "matter_name": {"type": "string", "example": "Example v Example"},
                        },
                    }
                }
            },
        }
    if endpoint == "documents.recommend_similar_documents":
        operation["parameters"].extend([
            {"name": "same_category", "in": "query", "description": "Restrict results to the source category.", "schema": {"type": "boolean", "default": True}, "example": True},
            {"name": "category", "in": "query", "description": "Explicit category filter.", "schema": {"type": "string"}, "example": "Contract"},
        ])
    return operation


def init_api_docs(app) -> Swagger:
    """Attach docs to every API view, then initialize Flasgger's UI/spec route."""
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.rule.startswith("/api/v1/docs"):
            continue
        view = app.view_functions[rule.endpoint]
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            # Flasgger consumes this metadata and regenerates JSON on each request
            # while debug mode is enabled.
            view = swag_from(deepcopy(_operation(rule, rule.endpoint, method)), methods=[method])(view)
        app.view_functions[rule.endpoint] = view

    template = {
        "openapi": "3.0.3",
        "info": {
            "title": "LegalVault REST API",
            "version": "1.0.0",
            "description": "Secure legal document storage, search, analytics, and AI processing API.",
            "contact": {"name": "LegalVault API Support"},
        },
        "servers": [{"url": "http://localhost:5000", "description": "Local development"}],
        "tags": TAGS,
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
            "schemas": SCHEMAS,
        },
    }
    config = {
        "headers": [],
        "specs": [{
            "endpoint": "openapi",
            "route": "/api/v1/openapi.json",
            "rule_filter": lambda rule: not rule.rule.startswith("/api/v1/docs"),
            "model_filter": lambda tag: True,
        }],
        "static_url_path": "/api/v1/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/v1/docs/",
        "openapi": "3.0.3",
    }
    return Swagger(app, template=template, config=config)
