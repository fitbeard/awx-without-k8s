from ..module_utils.aap_object import AAPObject

__metaclass__ = type

API_PREFIX = "/api/"


class AAPService(AAPObject):
    API_ENDPOINT_NAME = "services"
    ITEM_TYPE = "service"

    def __init__(self, module, params=None, **kwargs):
        super().__init__(module, params, **kwargs)
        self.service_cluster = None
        self.http_port = None

    def manage(self, **kwargs):
        if self.present():
            if self.params.get('service_cluster') is not None:
                self.get_service_cluster()
            if self.params.get('http_port') is not None:
                self.get_http_port()

        super().manage(**kwargs)

    def get_service_cluster(self):
        from ..module_utils.aap_service_cluster import AAPServiceCluster

        cluster_params = {self.module.IDENTITY_FIELDS['service_clusters']: self.params.get('service_cluster'), "state": self.STATE_EXISTS}

        self.service_cluster = AAPServiceCluster(module=self.module, params=cluster_params)

        self.service_cluster.manage(auto_exit=False, fail_when_not_exists=True)

    def get_http_port(self):
        from ..module_utils.aap_http_port import AAPHttpPort

        params = {self.module.IDENTITY_FIELDS['http_ports']: self.params.get('http_port'), "state": self.STATE_EXISTS}

        self.http_port = AAPHttpPort(module=self.module, params=params)

        self.http_port.manage(auto_exit=False, fail_when_not_exists=True)

    def unique_field(self):
        return self.module.IDENTITY_FIELDS["services"]

    def set_new_fields(self):
        self.set_name_field()

        api_slug = self.params.get('api_slug')
        if api_slug is not None:
            self.new_fields['api_slug'] = api_slug

        description = self.params.get('description')
        if description is not None:
            self.new_fields['description'] = description

        gateway_path = self.get_gateway_path()
        if gateway_path is not None:
            self.new_fields['gateway_path'] = gateway_path

        if self.http_port:
            http_port_id = (self.http_port.data or {}).get('id')
            if http_port_id is not None:
                self.new_fields['http_port'] = http_port_id

        if self.service_cluster:
            service_cluster_id = (self.service_cluster.data or {}).get('id')
            if service_cluster_id is not None:
                self.new_fields['service_cluster'] = service_cluster_id

        enable_gateway_auth = self.params.get('enable_gateway_auth')
        if enable_gateway_auth is not None:
            self.new_fields['enable_gateway_auth'] = enable_gateway_auth

        enable_mtls = self.params.get('enable_mtls')
        if enable_mtls is not None:
            self.new_fields['enable_mtls'] = enable_mtls

        is_service_https = self.params.get('is_service_https')
        if is_service_https is not None:
            self.new_fields['is_service_https'] = is_service_https

        service_path = self.params.get('service_path')
        if service_path is not None:
            self.new_fields['service_path'] = service_path

        service_port = self.params.get('service_port')
        if service_port is not None:
            self.new_fields['service_port'] = service_port

        order = self.params.get('order')
        if order is not None:
            self.new_fields['order'] = order

        node_tags = self.params.get('node_tags')
        if node_tags is not None:
            self.new_fields['node_tags'] = node_tags

    def get_gateway_path(self):
        if self.data:
            gateway_path = self.data['gateway_path']
        else:
            api_slug = self.params.get('api_slug')
            # Taken from:
            # https://github.com/ansible/aap-gateway/blob/382b27f458b5f957b49b2e8d4c86a72cc36eebfa/aap_gateway_api/models/service.py#L248  # noqa
            if api_slug == 'gateway':
                gateway_path = '/'
            elif api_slug:
                gateway_path = API_PREFIX + api_slug + "/"
            else:
                gateway_path = None
        return gateway_path
