import importlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bson import ObjectId
from flask_jwt_extended import create_access_token


class DocumentUploadFailureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["MONGO_URI"] = "mongodb://localhost:27017"
        sys.modules.pop("app", None)
        with patch("models.database.MongoClient", return_value=MagicMock()):
            module = importlib.import_module("app")
        module.app.config.update(TESTING=True)
        cls.app = module.app
        cls.user_id = str(ObjectId())

    def setUp(self):
        self.upload_directory = tempfile.TemporaryDirectory()
        self.app.config["UPLOAD_FOLDER"] = self.upload_directory.name
        self.client = self.app.test_client()
        self.user = {"_id": self.user_id, "email": "tester@example.com"}
        self.auth_patcher = patch(
            "utils.auth_middleware.find_user_by_id",
            return_value=self.user,
        )
        self.auth_patcher.start()

        with self.app.app_context():
            self.token = create_access_token(identity=self.user_id)

    def tearDown(self):
        self.auth_patcher.stop()
        self.upload_directory.cleanup()

    def test_rejects_unsupported_file_type(self):
        response = self.client.post(
            "/documents/upload",
            data={"file": (io.BytesIO(b"not a legal document"), "evidence.jpg")},
            headers={"Authorization": f"Bearer {self.token}"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"message": "Only PDF and DOCX files are allowed."},
        )
        self.assertEqual(list(Path(self.upload_directory.name).iterdir()), [])

    @patch("routes.documents.create_document")
    @patch("routes.documents.extract_text", side_effect=ValueError("corrupted file"))
    def test_cleans_up_file_when_text_extraction_fails(
        self, extract_text_mock, create_document_mock
    ):
        response = self.client.post(
            "/documents/upload",
            data={"file": (io.BytesIO(b"corrupted pdf content"), "corrupted.pdf")},
            headers={"Authorization": f"Bearer {self.token}"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.get_json(),
            {"message": "Unable to extract text from this document."},
        )
        extract_text_mock.assert_called_once()
        create_document_mock.assert_not_called()
        self.assertEqual(list(Path(self.upload_directory.name).iterdir()), [])


if __name__ == "__main__":
    unittest.main()