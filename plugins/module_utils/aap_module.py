from __future__ import absolute_import, division, print_function

__metaclass__ = type

import base64

# import os
import time

# from ansible.module_utils._text import to_bytes, to_native, to_text
# import os.path
# from socket import gethostbyname
from json import dumps, loads

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.http_cookiejar import CookieJar

# For Later
# from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import quote, urlencode, urlparse
from ansible.module_utils.urls import ConnectionError, Request, SSLValidationError  # fetch_file,

# import email.mime.multipart
# import email.mime.application


class ItemNotDefined(Exception):
    pass


class AAPModuleError(Exception):
    """API request error exception.

    :param error_message: Error message.
    :type error_message: str
    """

    def __init__(self, error_message):
        """Initialize the object."""
        self.error_message = error_message

    def __str__(self):
        """Return the error message."""
        return self.error_message


class AAPModule(AnsibleModule):
    url = None
    session = None
    AUTH_ARGSPEC = dict(
        gateway_hostname=dict(
            required=False,
            aliases=["aap_hostname"],
            fallback=(env_fallback, ["GATEWAY_HOSTNAME", "AAP_HOSTNAME"]),
        ),
        gateway_username=dict(required=False, aliases=["aap_username"], fallback=(env_fallback, ["GATEWAY_USERNAME", "AAP_USERNAME"])),
        gateway_password=dict(no_log=True, required=False, aliases=["aap_password"], fallback=(env_fallback, ["GATEWAY_PASSWORD", "AAP_PASSWORD"])),
        gateway_validate_certs=dict(
            aliases=["validate_certs", "aap_validate_certs"],
            type="bool",
            required=False,
            fallback=(env_fallback, ["GATEWAY_VERIFY_SSL", "AAP_VALIDATE_CERTS"]),
        ),
        gateway_token=dict(
            type="raw",
            aliases=["aap_token"],
            no_log=True,
            required=False,
            fallback=(env_fallback, ["GATEWAY_API_TOKEN", 'AAP_TOKEN']),
        ),
        gateway_request_timeout=dict(
            aliases=["request_timeout", "aap_request_timeout"],
            type="float",
            required=False,
            fallback=(env_fallback, ["GATEWAY_REQUEST_TIMEOUT", "AAP_REQUEST_TIMEOUT"]),
        ),
    )
    ENCRYPTED_STRING = "$encrypted$"
    product_name = "automation platform gateway"
    short_params = {
        "host": "gateway_hostname",
        "username": "gateway_username",
        "password": "gateway_password",
        "verify_ssl": "gateway_validate_certs",
        "request_timeout": "gateway_request_timeout",
        "oauth_token": "gateway_token",
    }
    IDENTITY_FIELDS = {
        "applications": ["name", "organization"],
        "authenticators": "name",
        "authenticator_maps": ["name", "authenticator"],
        "authenticator_users": "authenticator_user_id",
        "ca_certificates": "name",
        "http_ports": "name",
        "routes": "name",
        "services": "name",
        "service_clusters": "name",
        "service_keys": "name",
        "service_nodes": "name",
        "service_types": "name",
        "organizations": "name",
        "teams": ["name", "organization"],
        "ui_plugin_routes": "name",
        "users": "username",
        "role_definitions": "name",
    }
    host = "127.0.0.1"
    username = None
    password = None
    verify_ssl = True
    request_timeout = 10
    oauth_token = None
    authenticated = False
    error_callback = None
    warn_callback = None

    def __init__(self, argument_spec=None, direct_params=None, error_callback=None, warn_callback=None, require_auth=True, **kwargs):
        full_argspec = {}
        if require_auth:
            full_argspec.update(AAPModule.AUTH_ARGSPEC)
        full_argspec.update(argument_spec)
        kwargs["supports_check_mode"] = True

        self.error_callback = error_callback
        self.warn_callback = warn_callback

        self.json_output = {"changed": False}

        if direct_params is not None:
            self.params = direct_params
        else:
            super(AAPModule, self).__init__(argument_spec=full_argspec, **kwargs)
        self.session = Request(cookies=CookieJar(), validate_certs=self.verify_ssl, timeout=self.request_timeout)

        # Parameters specified on command line will override settings in any config
        for short_param, long_param in self.short_params.items():
            direct_value = self.params.get(long_param)
            if direct_value is not None:
                setattr(self, short_param, direct_value)

        # Perform magic depending on whether ah_token is a string or a dict
        if self.params.get("gateway_token"):
            token_param = self.params.get("gateway_token")
            if isinstance(token_param, dict):
                if "token" in token_param:
                    self.oauth_token = self.params.get("gateway_token")["token"]
                else:
                    self.fail_json(msg="The provided dict in gateway_token did not properly contain the token entry")
            elif isinstance(token_param, string_types):
                self.oauth_token = self.params.get("gateway_token")
            else:
                error_msg = "The provided gateway_token type was not valid ({0}). Valid options are str or dict.".format(type(token_param).__name__)
                self.fail_json(msg=error_msg)

        # Perform some basic validation
        self.host_url = urlparse(self.validate_url(self.host))

        # Start Session
        self.session.headers.update(
            {
                "referer": self.host,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        if "update_secrets" in self.params:
            self.update_secrets = self.params.pop("update_secrets")
        else:
            self.update_secrets = True

        # Auth
        self.authenticate()

    def authenticate(self):
        """Authenticate with the API."""

        url = self.build_url("")  # login
        try:
            self.make_request_raw_reponse("GET", url)
        except AAPModuleError as e:
            self.fail_json(msg="Authentication error: {error}".format(error=e))
        if self.oauth_token:
            try:
                header = {"Authorization": "Bearer {0}".format(self.oauth_token)}
                self.make_request("GET", url)
                self.session.headers.update(header)
                self.authenticated = True
            except AAPModuleError as e:
                self.fail_json(msg="Authentication with cookie error: {error}".format(error=e))
        elif self.username and self.password:
            try:
                basic_str = base64.b64encode("{0}:{1}".format(self.username, self.password).encode("ascii"))
                header = {"Authorization": "Basic {0}".format(basic_str.decode("ascii"))}
                self.make_request("GET", url)
                self.session.headers.update(header)
                self.authenticated = True
            except AAPModuleError as e:
                self.fail_json(msg="Authentication error: {error}".format(error=e))

    def validate_url(self, url):
        # Perform some basic validation
        if not url.startswith(("https://", "http://")):
            validated_url = f"https://{url}"
        else:
            validated_url = url

        # Try to parse the hostname as a url
        try:
            urlparse(validated_url)
        except Exception as e:
            self.fail_json(msg="Unable to parse host as a URL ({1}): {0}".format(validated_url, e))
        return validated_url

    def fail_json(self, **kwargs):
        # Try to log out if we are authenticated
        if self.error_callback:
            self.error_callback(**kwargs)
        else:
            super(AAPModule, self).fail_json(**kwargs)

    def exit_json(self, **kwargs):
        # Try to log out if we are authenticated
        super(AAPModule, self).exit_json(**kwargs)

    def warn(self, warning):
        if self.warn_callback is not None:
            self.warn_callback(warning)
        else:
            super(AAPModule, self).warn(warning)

    def build_url(self, endpoint, query_params=None):
        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = "/{0}".format(endpoint)
        if not endpoint.startswith("/api/"):
            endpoint = "api/gateway/v1{0}".format(endpoint)
        if not endpoint.endswith("/") and "?" not in endpoint:
            endpoint = "{0}/".format(endpoint)

        # Update the URL path with the endpoint
        url = self.host_url._replace(path=endpoint)

        if query_params:
            url = url._replace(query=urlencode(query_params))
        return url

    def make_request(self, method, url, wait_for_task=True, **kwargs):
        """Perform an API call and return the data.

        :param method: GET, PUT, POST, or DELETE
        :type method: str
        :param url: URL to the API endpoint
        :type url: :py:class:``urllib.parse.ParseResult``
        :param kwargs: Additionnal parameter to pass to the API (headers, data
                       for PUT and POST requests, ...)

        :raises AAPModuleError: The API request failed.

        :return: A dictionary with two entries: ``status_code`` provides the
                 API call returned code and ``json`` provides the returned data
                 in JSON format.
        :rtype: dict
        """

        response = self.make_request_raw_reponse(method, url, **kwargs)
        try:
            response_body = response.read()
        except Exception as e:
            self.fail_json(msg="{error}".format(error=(response["json"])))
            if response["json"]["non_field_errors"]:
                raise AAPModuleError("Errors occurred with request (HTTP 400). Errors: {errors}".format(errors=response["json"]["non_field_errors"]))
            elif response["json"]["errors"]:
                raise AAPModuleError("Errors occurred with request (HTTP 400). Errors: {errors}".format(errors=response["json"]["errors"]))
            elif response["text"]:
                raise AAPModuleError("Errors occurred with request (HTTP 400). Errors: {errors}".format(errors=response["text"]))
            raise AAPModuleError("Failed to read response body: {error}".format(error=e))

        response_json = {}
        if response_body and response_body != "":
            try:
                response_json = loads(response_body)
            except Exception as e:
                raise AAPModuleError("Failed to parse the response json: {0}".format(e))

        # A background task has been triggered. Check if the task is completed
        if response.status == 202 and "task" in response_json and wait_for_task:
            url = url._replace(path=response_json["task"], query="")
            for _count in range(5):
                time.sleep(3)
                bg_task = self.make_request("GET", url)
                if "state" in bg_task["json"] and bg_task["json"]["state"].lower().startswith("complete"):
                    break
            else:
                if "state" in bg_task["json"]:
                    raise AAPModuleError(
                        "Failed to get the status of the remote task: {task}: last status: {status}".format(
                            task=response_json["task"], status=bg_task["json"]["state"]
                        )
                    )
                raise AAPModuleError("Failed to get the status of the remote task: {task}".format(task=response_json["task"]))

        return {"status_code": response.status, "json": response_json}

    def make_request_raw_reponse(self, method, url, **kwargs):
        # In case someone is calling us directly; make sure we were given a method, let's not just assume a GET
        if not method:
            raise Exception("The HTTP method must be defined")

        # headers = kwargs.get("headers", self.headers)

        # May need reworked
        data = None  # Important, if content type is not JSON, this should not be dict type
        # if headers.get("Content-Type", "") == "application/x-www-form-urlencoded":
        #     data = kwargs.get("data", None)
        # elif headers.get("Content-Type", "") == "application/json":
        #     data = dumps(kwargs.get("data", {}))
        # elif kwargs.get("binary", False):
        #     data = kwargs.get("data", None)

        # set default response
        # if url == self.authorized_url:
        #     self.fail_json(msg="{error}".format(error=self.verify_ssl))

        # set default response
        response = {}
        if self.session.headers.get("Content-Type", "") == "application/json":
            data = dumps(kwargs.get("data", {}))
        elif kwargs.get("binary", False):
            data = kwargs.get("data", None)

        if method.upper() in {'PUT', 'POST', 'DELETE', 'PATCH'} and self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        try:
            response = self.session.open(
                method,
                url.geturl(),
                validate_certs=self.verify_ssl,
                timeout=self.request_timeout,
                follow_redirects=True,
                data=data,
            )
        except SSLValidationError as ssl_err:
            self.fail_json(msg="Could not establish a secure connection to your host ({1}): {0}.".format(url.netloc, ssl_err))
        except ConnectionError as con_err:
            self.fail_json(msg="There was a network error of some kind trying to connect to your host ({1}): {0}.".format(url.netloc, con_err))
        except HTTPError as he:
            # Sanity check: Did the server send back some kind of internal error?
            if he.code >= 500:
                self.fail_json(msg="The host sent back a server error ({1}): {0}. Please check the logs and try again later".format(url.path, he))
            # Sanity check: Did we fail to authenticate properly?  If so, fail out now; this is always a failure.
            elif he.code == 401:
                self.fail_json(
                    msg="Invalid {0} authentication credentials for url:{1} headers:{2} (HTTP 401).".format(self.product_name, url, self.session.headers)
                )
            # Sanity check: Did we get a forbidden response, which means that the user isn't allowed to do this? Report that.
            elif he.code == 403:
                self.fail_json(msg="You don't have permission to {2} , {1} to {0} (HTTP 403).".format(url, method, self.session.headers))
            # Sanity check: Did we get a 404 response?
            # Requests with primary keys will return a 404 if there is no response, and we want to consistently trap these.
            elif he.code == 404:
                if kwargs.get("return_none_on_404", False):
                    return None
                if kwargs.get("return_errors_on_404", False):
                    page_data = he.read()
                    try:
                        return {"status_code": he.code, "json": loads(page_data)}
                    # JSONDecodeError only available on Python 3.5+
                    except ValueError:
                        return {"status_code": he.code, "text": page_data}
                self.fail_json(msg="The requested object could not be found at {0}, response: {1}".format(url.path, he))

            # Sanity check: Did we get a 405 response?
            # A 405 means we used a method that isn't allowed. Usually this is a bad request, but it requires special treatment because the
            # API sends it as a logic error in a few situations (e.g. trying to cancel a job that isn't running).
            elif he.code == 405:
                self.fail_json(
                    msg="The {0} server says you can't make a request with the {1} method to this endpoint {2}".format(self.product_name, method, url.path)
                )
            # Sanity check: Did we get some other kind of error?  If so, write an appropriate error message.
            elif he.code >= 400:
                # We are going to return a 400 so the module can decide what to do with it
                page_data = he.read()
                try:
                    return {"status_code": he.code, "json": loads(page_data)}
                # JSONDecodeError only available on Python 3.5+
                except ValueError:
                    return {"status_code": he.code, "text": page_data}
            elif he.code == 204 and method == "DELETE":
                # A 204 is a normal response for a delete function
                pass
            else:
                self.fail_json(msg="Unexpected return code when calling {0}: {1}".format(url, he))
        except Exception as e:
            self.fail_json(msg="There was an unknown error when trying to connect to {2}: {0} {1}".format(type(e).__name__, e, url))

        return response

    def create_or_update_if_needed(
        self,
        existing_item,
        new_item,
        endpoint=None,
        item_type="unknown",
        on_create=None,
        on_update=None,
        auto_exit=True,
        associations=None,
        require_id=True,
        fixed_url=None,
    ):
        if existing_item:
            return self.update_if_needed(
                existing_item,
                new_item,
                on_update=on_update,
                auto_exit=auto_exit,
                associations=associations,
                require_id=require_id,
                fixed_url=fixed_url,
            )
        else:
            return self.create_if_needed(
                existing_item,
                new_item,
                endpoint,
                on_create=on_create,
                item_type=item_type,
                auto_exit=auto_exit,
                associations=associations,
            )

    def create_if_needed(
        self,
        existing_item,
        new_item,
        endpoint,
        on_create=None,
        auto_exit=True,
        item_type="unknown",
        associations=None,
    ):
        # This will exit from the module on its own
        # If the method successfully creates an item and on_create param is defined,
        #    the on_create parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item is already defined (so no create needs to happen)
        #    2. The response from automation platform gateway from calling the patch on the endpont. It's up to you
        #       to process the response and exit from the module
        # Note: common error codes from the automation platform gateway API can cause the module to fail
        if not endpoint:
            self.fail_json(msg="Unable to create new {0} due to missing endpoint".format(item_type))
        item_url = self.build_url(endpoint)
        if existing_item:
            try:
                item_url = self.build_url(existing_item["url"])
            except KeyError as ke:
                self.fail_json(msg="Unable to process create of item due to missing data {0}".format(ke))
        else:
            # If we don't have an existing_item, we can try to create it
            # We have to rely on item_type being passed in since we don't have an existing item that declares its type
            # We will pull the item_name out from the new_item, if it exists
            response = {}
            item_name = self.get_item_name(new_item, allow_unknown=True)
            response = self.make_request("POST", item_url, **{"data": new_item})

            if response["status_code"] in [200, 201]:
                self.json_output["name"] = "unknown"
                for key in ("name", "username", "identifier", "hostname"):
                    if key in response["json"]:
                        self.json_output["name"] = response["json"][key]
                        self.json_output[key] = response["json"][key]
                # # Special case: objects without a natural "name" (e.g., role_team_assignments)
                sf = response["json"].get("summary_fields") or {}
                if self.json_output["name"] == "unknown" and sf:
                    self.json_output["summary_fields"] = response["json"]["summary_fields"]

                if item_type != "token":
                    self.json_output["id"] = response["json"]["id"]
                self.json_output["changed"] = True
            else:
                if "json" in response and "__all__" in response["json"]:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response["json"]["__all__"][0]))
                elif "json" in response:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response["json"]))
                else:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response["status_code"]))

        # Process any associations with this item
        if associations is not None:
            for association_type in associations:
                sub_endpoint = "{0}{1}/".format(item_url, association_type)
                self.modify_associations(sub_endpoint, associations[association_type])

        # If we have an on_create method and we actually changed something we can call on_create
        if on_create is not None and self.json_output["changed"]:
            on_create(self, response["json"])
        elif auto_exit:
            self.exit_json(**self.json_output)
        elif not existing_item:
            last_data = response["json"]
            return last_data
        return None

    def update_if_needed(
        self,
        existing_item,
        new_item,
        on_update=None,
        auto_exit=True,
        associations=None,
        require_id=True,
        fixed_url=None,
    ):
        # This will exit from the module on its own
        # If the method successfully updates an item and on_update param is defined,
        #   the on_update parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item does not need to be updated
        #    2. The response from automation platform gateway from patching to the endpoint. It's up to you to process the response and exit from the module.
        # Note: common error codes from the automation platform gateway API can cause the module to fail
        response = None
        if existing_item:
            try:
                item_url = self.build_url(existing_item["url"])
                self.json_output["id"] = require_id and existing_item["id"]
            except KeyError as ke:
                self.fail_json(msg="Unable to process create of item due to missing data {0}".format(ke))

            # Check to see if anything within the item requires the item to be updated
            needs_patch = self.objects_could_be_different(existing_item, new_item)

            if needs_patch:
                response = self.make_request("PATCH", item_url, **{"data": new_item})
                if response["status_code"] == 200:
                    # compare apples-to-apples, old API data to new API data
                    # but do so considering the fields given in parameters
                    self.json_output["changed"] = self.objects_could_be_different(
                        existing_item,
                        response["json"],
                        field_set=new_item.keys(),
                        warning=True,
                    )
                elif "json" in response and "__all__" in response["json"]:
                    self.fail_json(msg=response["json"]["__all__"])
                else:
                    self.fail_json(
                        **{
                            "msg": "Unable to update {0}, see response".format(item_url),
                            "response": response,
                            "input": new_item,
                        }
                    )

        else:
            raise RuntimeError("update_if_needed called incorrectly without existing_item")

        # Process any associations with this item
        if associations is not None:
            for association_type, id_list in associations.items():
                endpoint = "{0}{1}/".format(item_url, association_type)
                self.modify_associations(endpoint, id_list)

        # If we change something and have an on_change call it
        if on_update is not None and self.json_output["changed"]:
            if response is None:
                last_data = existing_item
            else:
                last_data = response["json"]
            on_update(self, last_data)
        elif auto_exit:
            self.exit_json(**self.json_output)
        else:
            if response is None:
                last_data = existing_item
            else:
                last_data = response["json"]
            return last_data

    def get_item_name(self, item, allow_unknown=False):
        if item:
            if "name" in item:
                return item["name"]

            for field_name in AAPModule.IDENTITY_FIELDS.values():
                if isinstance(field_name, list):
                    found = True
                    for sub_field_name in field_name:
                        if sub_field_name not in item:
                            found = False

                    if found:
                        return '_'.join([str(item[sub_field_name]) for sub_field_name in field_name])
                else:
                    if field_name in item:
                        return item[field_name]

        if allow_unknown:
            return "unknown"

        if item:
            self.fail_json(msg="Cannot determine identity field for {0} object.".format(item.get("type", "unknown")))
        else:
            self.fail_json(msg="Cannot determine identity field for Undefined object.")

    def get_endpoint(self, endpoint, *args, **kwargs):
        url = self.build_url(endpoint, query_params=kwargs.get('data'))
        return self.make_request("GET", url, **kwargs)

    def get_all_endpoint(self, endpoint, *args, **kwargs):
        url = self.build_url(endpoint)
        response = self.make_request("GET", url, *args, **kwargs)
        if "next" not in response["json"]:
            raise RuntimeError("Expected list from API at {0}, got: {1}".format(endpoint, response))
        next_page = response["json"]["next"]

        if response["json"]["count"] > 10000:
            self.fail_json(msg="The number of items being queried for is higher than 10,000.")

        while next_page is not None:
            next_response = self.make_request("GET", next_page)
            response["json"]["results"] = response["json"]["results"] + next_response["json"]["results"]
            next_page = next_response["json"]["next"]
            response["json"]["next"] = next_page
        return response

    @staticmethod
    def get_name_field_from_endpoint(endpoint):
        unique = AAPModule.IDENTITY_FIELDS.get(endpoint)
        if isinstance(unique, list):
            return unique[0]

        return unique or "name"

    def get_one(self, endpoint, name_or_id=None, allow_none=True, check_exists=False, **kwargs):
        new_kwargs = kwargs.copy()
        response = None

        # A named URL is pretty unique so if we have a ++ in the name then lets start by looking for that
        # This also needs to go first because if there was data passed in kwargs and we do the next lookup first there may be results
        if name_or_id is not None and "++" in name_or_id:
            # Maybe someone gave us a named URL so lets see if we get anything from that.
            url_quoted_name = quote(name_or_id, safe="+")
            url = self.build_url("{0}/{1}/".format(endpoint, url_quoted_name))
            named_response = self.make_request("GET", url)

            if named_response["status_code"] == 200 and "json" in named_response:
                # We found a named item but we expect to deal with a list view so mock that up
                response = {
                    "json": {
                        "count": 1,
                        "results": [named_response["json"]],
                    }
                }

        # Since we didn't have a named URL, lets try and find it with a general search
        if response is None:
            if name_or_id:
                name_field = self.get_name_field_from_endpoint(endpoint)
                new_data = kwargs.get("data", {}).copy()
                if name_field in new_data:
                    self.fail_json(msg="You can't specify the field {0} in your search data if using the name_or_id field".format(name_field))

                try:
                    new_data["or__id"] = int(name_or_id)
                    new_data["or__{0}".format(name_field)] = name_or_id
                except ValueError:
                    # If we get a value error, then we didn't have an integer so we can just pass and fall down to the fail
                    new_data[name_field] = name_or_id
                new_kwargs["data"] = new_data

            url = self.build_url(endpoint, query_params=new_kwargs.get("data"))
            response = self.make_request("GET", url)

            if response["status_code"] != 200:
                fail_msg = "Got a {0} response when trying to get one from {1}".format(response["status_code"], endpoint)
                if "detail" in response.get("json", {}):
                    fail_msg += ", detail: {0}".format(response["json"]["detail"])
                self.fail_json(msg=fail_msg)

            if "count" not in response["json"] or "results" not in response["json"]:
                self.fail_json(msg="The endpoint did not provide count and results")

        if response["json"]["count"] == 0:
            if allow_none:
                return None
            else:
                self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))
        elif response["json"]["count"] > 1:
            if name_or_id:
                # Since we did a name or ID search and got > 1 return something if the id matches
                for asset in response["json"]["results"]:
                    if str(asset["id"]) == name_or_id:
                        return asset
            # We got > 1 and either didn't find something by ID (which means multiple names)
            # Or we weren't running with a or search and just got back too many to begin with.
            self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))

        if check_exists:
            self.json_output["id"] = response["json"]["results"][0]["id"]
            self.exit_json(**self.json_output)
        return response["json"]["results"][0]

    def fail_wanted_one(self, response, endpoint, query_params):
        sample = response.copy()
        if len(sample["json"]["results"]) > 1:
            sample["json"]["results"] = sample["json"]["results"][:2] + ["...more results snipped..."]
        url = self.build_url(endpoint, query_params)
        self.fail_json(
            msg="Request to {0} returned {1} items, expected 1".format(url, response["json"]["count"]),
            query=query_params,
            response=sample,
            total_results=response["json"]["count"],
        )

    def objects_could_be_different(self, old, new, field_set=None, warning=False):
        if field_set is None:
            field_set = set(fd for fd in new.keys() if fd not in ("modified", "related", "summary_fields"))
        for field in field_set:
            new_field = new.get(field, None)
            old_field = old.get(field, None)
            if old_field == new_field:
                # This is a short circuit and protects us in the case of both being None
                continue
            elif self.has_encrypted_values(new_field) or field not in new:
                if self.update_secrets or (not self.fields_could_be_same(old_field, new_field)):
                    # case of 'field not in new' - user password write-only field that API will not display
                    self._encrypted_changed_warning(field, old, warning=warning)
                    return True
            else:
                if self.update_secrets or (not self.fields_could_be_same(old_field, new_field)):
                    return True  # Something doesn't match, or something might not match
        return False

    @staticmethod
    def has_encrypted_values(obj):
        """Returns True if JSON-like python content in obj has $encrypted$
        anywhere in the data as a value
        """
        if isinstance(obj, dict):
            for val in obj.values():
                if AAPModule.has_encrypted_values(val):
                    return True
        elif isinstance(obj, list):
            for val in obj:
                if AAPModule.has_encrypted_values(val):
                    return True
        return False

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.warn(
            "The field {0} of {1} {2} has encrypted data and may inaccurately report task is changed.".format(
                field, old.get("type", "unknown"), old.get("id", "unknown")
            )
        )

    def delete_if_needed(self, existing_item, on_delete=None, auto_exit=True):
        # This will exit from the module on its own.
        # If the method successfully deletes an item and on_delete param is defined,
        #   the on_delete parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #   1. None if the existing_item is not defined (so no delete needs to happen)
        #   2. The response from automation platform gateway from calling the delete on the endpont.
        #      It's up to you to process the response and exit from the module
        # Note: common error codes from the automation platform gateway API can cause the module to fail
        if existing_item:
            try:
                item_url = self.build_url(existing_item["url"])
                item_id = existing_item["id"]
                item_name = self.get_item_name(existing_item, allow_unknown=True)
            except KeyError as ke:
                self.fail_json(msg="Unable to process delete of item due to missing data {0}".format(ke))
            response = self.make_request("DELETE", item_url)
        else:
            if auto_exit:
                self.exit_json(**self.json_output)
            else:
                return self.json_output

        if response["status_code"] in [202, 204]:
            if on_delete:
                on_delete(self, response["json"])
            self.json_output["changed"] = True
            self.json_output["id"] = item_id
            if auto_exit:
                self.exit_json(**self.json_output)
            else:
                return self.json_output
        else:
            if "json" in response and "__all__" in response["json"]:
                self.fail_json(msg="Unable to delete {0}: {1}".format(item_name, response["json"]["__all__"][0]))
            elif "json" in response:
                # This is from a project delete (if there is an active job against it)
                if "error" in response["json"]:
                    self.fail_json(msg="Unable to delete {0}: {1}".format(item_name, response["json"]["error"]))
                else:
                    self.fail_json(msg="Unable to delete {0}: {1}".format(item_name, response["json"]))
            else:
                self.fail_json(msg="Unable to delete {0}: {1}".format(item_name, response["status_code"]))

    def get_enforced_defaults(self, endpoint, *args, **kwargs):
        endpoint_defaults = self.make_request("OPTIONS", self.build_url(endpoint))["json"]["actions"]["POST"]

        self.fail_json(msg="This is not yet implemented due to missing defaults: {error}".format(error=endpoint_defaults))
        # default_fields[endpoint]['new_fields'], default_fields[endpoint]['association_fields']
        return endpoint_defaults

    @staticmethod
    def fields_could_be_same(old_field, new_field):
        """Treating $encrypted$ as a wild card,
        return False if the two values are KNOWN to be different
        return True if the two values are the same, or could potentially be the same,
        depending on the unknown $encrypted$ value or sub-values
        """
        if isinstance(old_field, dict) and isinstance(new_field, dict):
            if set(old_field.keys()) != set(new_field.keys()):
                return False
            for key in new_field.keys():
                if not AAPModule.fields_could_be_same(old_field[key], new_field[key]):
                    return False
            return True  # all sub-fields are either equal or could be equal
        else:
            if old_field == AAPModule.ENCRYPTED_STRING:
                return True
            return bool(new_field == old_field)
