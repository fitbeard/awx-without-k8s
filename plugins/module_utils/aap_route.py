from ..module_utils.aap_service import AAPService

__metaclass__ = type


class AAPRoute(AAPService):
    API_ENDPOINT_NAME = "routes"
    ITEM_TYPE = "route"

    def unique_field(self):
        return self.module.IDENTITY_FIELDS["routes"]

    def get_gateway_path(self):
        if self.data:
            return self.data['gateway_path']
        return self.params.get('gateway_path')
