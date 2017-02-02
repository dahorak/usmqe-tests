
"""
Basic REST API.
"""

import pytest
import json

LOGGER = pytest.get_logger("api_base", module=True)


class ApiBase(object):
    """ Basic class for REST API.
    """

    default_asserts = {
        "cookies": None,
        "ok": True,
        "reason": 'OK',
        "status": 200,
    }

    @staticmethod
    def print_req_info(resp):
        """ Print debug information.

        Args:
            resp: response
        """
        LOGGER.debug("request.url:  {}".format(resp.request.url))
        LOGGER.debug("request.method:  {}".format(resp.request.method))
        LOGGER.debug("request.body:  {}".format(resp.request.body))
        LOGGER.debug("request.headers:  {}".format(resp.request.headers))
        LOGGER.debug("response.cookies: {}".format(resp.cookies))
        # LOGGER.debug("response.content: {}".format(resp.content))
        LOGGER.debug("response.headers: {}".format(resp.headers))
        # try:
        #     LOGGER.debug(
        #         "response.json:    {}".format(resp.json(encoding='unicode')))
        # except ValueError:
        #     LOGGER.debug("response.json:    ")
        LOGGER.debug("response.ok:      {}".format(resp.ok))
        LOGGER.debug("response.reason:  {}".format(resp.reason))
        LOGGER.debug("response.status:  {}".format(resp.status_code))
        LOGGER.debug("response.text:    {}".format(resp.text))

    @staticmethod
    def check_response(resp, asserts_in=None):
        """ Check default asserts.

        It checks: *ok*, *status*, *reason*.
        Args:
            resp: response to check
            asserts_in: asserts that are compared with response
        """

        asserts = ApiBase.default_asserts.copy()
        if asserts_in:
            asserts.update(asserts_in)
        try:
            json.dumps(resp.json(encoding='unicode'))
        except ValueError as e:
            pytest.check(False, issue="Bad response json format: {}".format(e.msg))
        pytest.check(
            resp.ok == asserts["ok"],
            "There should be ok == {}".format(str(asserts["ok"])))
        pytest.check(resp.status_code == asserts["status"],
                     "Status code should equal to {}".format(asserts["status"]))
        pytest.check(resp.reason == asserts["reason"],
                     "Reason should equal to {}".format(asserts["reason"]))

    @staticmethod
    def check_dict(data, schema):
        """
        Check dictionary schema (keys, value types).

        Parameters:
          data - dictionary to check
          schema - dictionary with keys and value types, e.g.:
                  {'name': str, 'size': int, 'tasks': dict}
        """
        LOGGER.debug("check_dict - data: {}".format(data))
        LOGGER.debug("check_dict - schema: []".format(schema))
        expected_keys = sorted(schema.keys())
        keys = sorted(data.keys())
        pytest.check(
            keys == expected_keys,
            "Data should contains keys: {}".format(expected_keys))
        for key in keys:
            pytest.check(key in expected_keys,
                         "Unknown key '{}' with value '{}' (type: '{}').".format(
                             key, data[key], type(data[key])))
            if key in expected_keys:
                pytest.check(isinstance(data[key], schema[key]))
