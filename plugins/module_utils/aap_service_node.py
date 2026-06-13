from ..module_utils.aap_object import AAPObject

__metaclass__ = type


class AAPServiceNode(AAPObject):
    API_ENDPOINT_NAME = "service_nodes"
    ITEM_TYPE = "service_node"

    def __init__(self, module, params=None, **kwargs):
        super().__init__(module, params, **kwargs)
        self.service_cluster = None

    def manage(self, **kwargs):
        if self.present() and self.params.get('service_cluster') is not None:
            self.get_service_cluster()

        super().manage(**kwargs)

    def get_service_cluster(self):
        from ..module_utils.aap_service_cluster import AAPServiceCluster

        cluster_params = {self.module.IDENTITY_FIELDS['service_clusters']: self.params.get('service_cluster'), "state": self.STATE_EXISTS}

        self.service_cluster = AAPServiceCluster(module=self.module, params=cluster_params)

        self.service_cluster.manage(auto_exit=False, fail_when_not_exists=True)

    def unique_field(self):
        return self.module.IDENTITY_FIELDS["service_nodes"]

    def set_new_fields(self):
        # Create the data that gets sent for create and update
        self.set_name_field()

        address = self.params.get('address')
        if address is not None:
            self.new_fields['address'] = address

        if self.service_cluster:
            service_cluster_id = (self.service_cluster.data or {}).get('id')
            if service_cluster_id is not None:
                self.new_fields['service_cluster'] = service_cluster_id

        tags = self.params.get('tags')
        if tags is not None:
            self.new_fields['tags'] = tags
