# -*- coding: utf8 -*-

import pytest

from usmqe.api.tendrlapi.common import TendrlAuth, login, logout


@pytest.fixture(scope="session")
def valid_session_credentials(request):
    """
    During setup phase, login default usmqe user account (username and password
    comes from usm.ini config file) and return requests auth object.
    Then during teardown logout the user to close the session.
    """
    auth = login(
        pytest.config.getini("usm_username"),
        pytest.config.getini("usm_password"))
    yield auth
    logout(auth=auth)


@pytest.fixture(
    scope="session",
    params=[
        "",
        None,
        "this_is_invalid_access_token_00000",
        "4e3459381b5b94fcd642fb0ca30eba062fbcc126a47c6280945a3405e018e824",
        ])
def invalid_session_credentials(request):
    """
    Return invalid access (for testing negative use cases), no login or logout
    is performed during setup or teardown.
    """
    username = pytest.config.getini("usm_username")
    invalid_token = request.param
    auth = TendrlAuth(token=invalid_token, username=username)
    return auth
