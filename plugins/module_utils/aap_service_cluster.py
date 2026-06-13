from ..module_utils.aap_object import AAPObject

__metaclass__ = type


class AAPServiceCluster(AAPObject):
    API_ENDPOINT_NAME = "service_clusters"
    ITEM_TYPE = "service_cluster"

    def __init__(self, module, params=None, **kwargs):
        super().__init__(module, params, **kwargs)
        self.service_type = None

    def manage(self, **kwargs):
        if self.present() and self.params.get('service_type') is not None:
            self.get_service_type()

        super().manage(**kwargs)

    def get_service_type(self):
        from ..module_utils.aap_service_type import AAPServiceType

        type_params = {self.module.IDENTITY_FIELDS['service_types']: self.params.get('service_type'), "state": self.STATE_EXISTS}

        self.service_type = AAPServiceType(module=self.module, params=type_params)

        self.service_type.manage(auto_exit=False, fail_when_not_exists=True)

    def unique_field(self):
        return self.module.IDENTITY_FIELDS['service_clusters']

    def set_new_fields(self):
        # Create the data that gets sent for create and update
        self.set_name_field()

        if self.service_type:
            service_type_id = (self.service_type.data or {}).get('id')
            if service_type_id is not None:
                self.new_fields['service_type'] = service_type_id

        outlier_detection_enabled = self.params.get('outlier_detection_enabled')
        if outlier_detection_enabled is not None:
            self.new_fields["outlier_detection_enabled"] = outlier_detection_enabled

        outlier_detection_consecutive_5xx = self.params.get('outlier_detection_consecutive_5xx')
        if outlier_detection_consecutive_5xx is not None:
            self.new_fields["outlier_detection_consecutive_5xx"] = outlier_detection_consecutive_5xx

        outlier_detection_interval_seconds = self.params.get('outlier_detection_interval_seconds')
        if outlier_detection_interval_seconds is not None:
            self.new_fields["outlier_detection_interval_seconds"] = outlier_detection_interval_seconds

        outlier_detection_base_ejection_time_seconds = self.params.get('outlier_detection_base_ejection_time_seconds')
        if outlier_detection_base_ejection_time_seconds is not None:
            self.new_fields["outlier_detection_base_ejection_time_seconds"] = outlier_detection_base_ejection_time_seconds

        outlier_detection_max_ejection_percent = self.params.get('outlier_detection_max_ejection_percent')
        if outlier_detection_max_ejection_percent is not None:
            self.new_fields["outlier_detection_max_ejection_percent"] = outlier_detection_max_ejection_percent

        health_checks_enabled = self.params.get('health_checks_enabled')
        if health_checks_enabled is not None:
            self.new_fields["health_checks_enabled"] = health_checks_enabled

        health_check_timeout_seconds = self.params.get('health_check_timeout_seconds')
        if health_check_timeout_seconds is not None:
            self.new_fields["health_check_timeout_seconds"] = health_check_timeout_seconds

        health_check_interval_seconds = self.params.get('health_check_interval_seconds')
        if health_check_interval_seconds is not None:
            self.new_fields["health_check_interval_seconds"] = health_check_interval_seconds

        health_check_unhealthy_threshold = self.params.get('health_check_unhealthy_threshold')
        if health_check_unhealthy_threshold is not None:
            self.new_fields["health_check_unhealthy_threshold"] = health_check_unhealthy_threshold

        health_check_healthy_threshold = self.params.get('health_check_healthy_threshold')
        if health_check_healthy_threshold is not None:
            self.new_fields["health_check_healthy_threshold"] = health_check_healthy_threshold

        auth_type = self.params.get('auth_type')
        if auth_type is not None:
            self.new_fields["auth_type"] = auth_type

        upstream_hostname = self.params.get('upstream_hostname')
        if upstream_hostname is not None:
            self.new_fields["upstream_hostname"] = upstream_hostname

        dns_discovery_type = self.params.get('dns_discovery_type')
        if dns_discovery_type is not None:
            self.new_fields["dns_discovery_type"] = dns_discovery_type

        dns_lookup_family = self.params.get('dns_lookup_family')
        if dns_lookup_family is not None:
            self.new_fields["dns_lookup_family"] = dns_lookup_family
