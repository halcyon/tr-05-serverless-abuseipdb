from http import HTTPStatus

from pytest import fixture
from unittest import mock
from requests.exceptions import SSLError

from .utils import headers
from tests.unit.mock_for_tests import (
    EXPECTED_RESPONSE_404_ERROR,
    EXPECTED_RESPONSE_500_ERROR,
    EXPECTED_RESPONSE_AUTH_ERROR,
    EXPECTED_RESPONSE_SSL_ERROR,
    ABUSE_401_RESPONSE,
    ABUSE_RESPONSE_MOCK,
    EXPECTED_AUTHORIZATION_HEADER_ERROR,
    EXPECTED_AUTHORIZATION_TYPE_ERROR,
    EXPECTED_JWT_STRUCTURE_ERROR,
    EXPECTED_JWT_PAYLOAD_STRUCTURE_ERROR,
    EXPECTED_WRONG_SECRET_KEY_ERROR,
    EXPECTED_MISSED_SECRET_KEY_ERROR
)


def routes():
    yield '/health'


@fixture(scope='module', params=routes(), ids=lambda route: f'POST {route}')
def route(request):
    return request.param


@fixture(scope='function')
def abuse_api_request():
    with mock.patch('requests.get') as mock_request:
        yield mock_request


def abuse_api_response(*, ok, status_error=None, payload=None):
    mock_response = mock.MagicMock()

    mock_response.ok = ok

    if ok:
        if not payload:
            payload = ABUSE_RESPONSE_MOCK

    else:
        mock_response.status_code = status_error
        mock_response.text = str(payload)
        mock_response.get_json.return_value = payload

    mock_response.json = lambda: payload

    return mock_response


def test_health_call_success(route, client, valid_jwt, abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)
    response = client.post(route, headers=headers(valid_jwt))
    assert response.status_code == HTTPStatus.OK


def test_health_call_auth_error(route, client, valid_jwt, abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(
        ok=False,
        status_error=HTTPStatus.UNAUTHORIZED,
        payload=ABUSE_401_RESPONSE
    )
    response = client.post(route, headers=headers(valid_jwt))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == EXPECTED_RESPONSE_AUTH_ERROR


def test_health_call_404(route, client, valid_jwt, abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(
        ok=False,
        status_error=HTTPStatus.NOT_FOUND
    )
    response = client.post(route, headers=headers(valid_jwt))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == EXPECTED_RESPONSE_404_ERROR


def test_health_call_500(route, client, valid_jwt, abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(
        ok=False,
        status_error=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    response = client.post(route, headers=headers(valid_jwt))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == EXPECTED_RESPONSE_500_ERROR


def test_health_call_ssl_error(route, client, valid_jwt, abuse_api_request):
    mock_exception = mock.MagicMock()
    mock_exception.reason.args.__getitem__().verify_message \
        = 'self signed certificate'
    abuse_api_request.side_effect = SSLError(mock_exception)

    response = client.post(route, headers=headers(valid_jwt))

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_RESPONSE_SSL_ERROR


def test_health_call_auth_header_error(route, client, valid_jwt,
                                       abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)

    response = client.post(route, headers={})

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_AUTHORIZATION_HEADER_ERROR


def test_health_call_auth_type_error(route, client, valid_jwt,
                                     abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)
    header = {
        'Authorization': 'Basic test_jwt'
    }

    response = client.post(route, headers=header)

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_AUTHORIZATION_TYPE_ERROR


def test_health_call_jwt_structure_error(route, client, valid_jwt,
                                         abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)
    header = {
        'Authorization': 'Bearer bad_jwt_token'
    }

    response = client.post(route, headers=header)

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_JWT_STRUCTURE_ERROR


def test_health_call_payload_structure_error(route, client,
                                             valid_jwt_with_wrong_payload,
                                             abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)

    response = client.post(
        route,
        headers=headers(valid_jwt_with_wrong_payload)
    )

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_JWT_PAYLOAD_STRUCTURE_ERROR


def test_health_call_wrong_secret_key_error(route, client, valid_jwt,
                                            abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)
    right_secret_key = client.application.secret_key
    client.application.secret_key = 'wrong_key'

    response = client.post(route, headers=headers(valid_jwt))

    client.application.secret_key = right_secret_key

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_WRONG_SECRET_KEY_ERROR


def test_health_call_missed_secret_key_error(route, client, valid_jwt,
                                             abuse_api_request):
    abuse_api_request.return_value = abuse_api_response(ok=True)
    right_secret_key = client.application.secret_key
    client.application.secret_key = None

    response = client.post(route, headers=headers(valid_jwt))

    client.application.secret_key = right_secret_key

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    assert data == EXPECTED_MISSED_SECRET_KEY_ERROR
