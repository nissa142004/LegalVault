"""Regression tests for Swagger UI and automatic Flask route discovery."""

import importlib
import re
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


def _openapi_path(flask_path: str) -> str:
    return re.sub(r"<(?:[^:>]+:)?([^>]+)>", r"{\1}", flask_path)


class OpenApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["MONGO_URI"] = "mongodb://localhost:27017"
        sys.modules.pop("app", None)
        with patch("models.database.MongoClient", return_value=MagicMock()):
            module = importlib.import_module("app")
        module.app.config.update(TESTING=True)
        cls.app = module.app

    def test_swagger_ui_and_openapi_spec(self):
        client = self.app.test_client()

        # Flask redirects the no-slash URL to Flasgger's canonical UI URL.
        self.assertIn(client.get("/api/v1/docs").status_code, {301, 302, 307, 308})
        self.assertEqual(client.get("/api/v1/docs/").status_code, 200)

        response = client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        spec = response.get_json()
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertIn("bearerAuth", spec["components"]["securitySchemes"])

        expected_paths = {
            _openapi_path(rule.rule)
            for rule in self.app.url_map.iter_rules()
            if rule.endpoint != "static"
            and not rule.endpoint.startswith("flasgger.")
            and not rule.rule.startswith(("/api/v1/", "/apidocs", "/oauth2-redirect"))
        }
        self.assertLessEqual(expected_paths, set(spec["paths"]))

        upload = spec["paths"]["/documents/upload"]["post"]
        self.assertIn("multipart/form-data", upload["requestBody"]["content"])
        self.assertIn("201", upload["responses"])

        document = spec["paths"]["/documents/{document_id}"]["get"]
        self.assertTrue(
            any(parameter["name"] == "document_id" for parameter in document["parameters"])
        )
        self.assertEqual(document["security"], [{"bearerAuth": []}])


if __name__ == "__main__":
    unittest.main()
