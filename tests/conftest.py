"""
Pytest configuration and fixtures for n8n MCP server tests.

Version: 0.1.0
Created: 2026-01-13
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run.

    This fixture runs automatically before all tests to ensure N8N_API_KEY
    is set, which is required for importing the server module.
    """
    # Set dummy API key for tests (server.py requires it at module import time)
    os.environ["N8N_API_KEY"] = "test_api_key_for_pytest"
    os.environ["N8N_BASE_URL"] = "https://n8n-backend.homelab.com"
