from ..module_utils.aap_object import AAPObject

__metaclass__ = type


class AAPServiceType(AAPObject):
    API_ENDPOINT_NAME = "service_types"
    ITEM_TYPE = "service_type"

    def unique_field(self):
        return self.module.IDENTITY_FIELDS['service_types']

    def set_new_fields(self):
        # Create the data that gets sent for create and update
        self.set_name_field()

        ping_url = self.params.get('ping_url')
        if ping_url is not None:
            self.new_fields["ping_url"] = ping_url

        login_path = self.params.get('login_path')
        if login_path is not None:
            self.new_fields["login_path"] = login_path

        logout_path = self.params.get('logout_path')
        if logout_path is not None:
            self.new_fields["logout_path"] = logout_path

        service_index_path = self.params.get('service_index_path')
        if service_index_path is not None:
            self.new_fields["service_index_path"] = service_index_path
