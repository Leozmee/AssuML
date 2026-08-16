"""Tests du client HTTP api_client — mock des appels HTTP."""

from unittest.mock import MagicMock, patch

import pytest

from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    get_clients,
    get_health,
    predict_complet,
)


class TestApiClientErrors:
    @patch("utils.api_client.requests.get")
    def test_connection_error_leve_unavailable(self, mock_get):
        import requests as req

        mock_get.side_effect = req.exceptions.ConnectionError
        with pytest.raises(ApiUnavailableError):
            get_health()

    @patch("utils.api_client.requests.get")
    def test_timeout_leve_api_timeout(self, mock_get):
        import requests as req

        mock_get.side_effect = req.exceptions.Timeout
        with pytest.raises(ApiTimeoutError):
            get_health()

    @patch("utils.api_client.requests.get")
    def test_http_error_leve_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"detail": "Non trouvé"}
        mock_get.return_value = mock_resp
        with pytest.raises(ApiError) as exc_info:
            get_clients()
        assert exc_info.value.status_code == 404


class TestApiClientSuccess:
    @patch("utils.api_client.requests.get")
    def test_get_health_retourne_dict(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_resp
        result = get_health()
        assert result["status"] == "ok"

    @patch("utils.api_client.requests.get")
    def test_header_api_key_envoye(self, mock_get, settings):
        settings.API_KEY = "test-key-123"
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp
        get_clients()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"]["X-API-Key"] == "test-key-123"

    @patch("utils.api_client.requests.post")
    def test_predict_complet_envoie_body(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "cout_predit": 5000.0,
            "score_risque": 0.3,
            "categorie_risque": "faible",
            "prime": 6000.0,
            "decision": "accepter",
        }
        mock_post.return_value = mock_resp
        payload = {
            "age": 30,
            "sexe": 0,
            "imc": 25.0,
            "enfants": 0,
            "fumeur": 0,
            "region": "southwest",
        }
        result = predict_complet(payload)
        assert result["cout_predit"] == 5000.0
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["age"] == 30
