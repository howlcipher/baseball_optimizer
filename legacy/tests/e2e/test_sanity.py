import pytest
from tests.e2e.helpers import E2EApiClient

def test_helper_import(api_client):
    # Verify that conftest's api_client fixture works and we can instantiate E2EApiClient with it
    client = E2EApiClient(api_client)
    assert client.client is not None
