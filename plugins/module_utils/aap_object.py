import json
import tempfile
from abc import abstractmethod

__metaclass__ = type


class AAPObject:
    API_ENDPOINT_NAME = ""
    ITEM_TYPE = ""

    STATE_ABSENT = "absent"
    STATE_EXISTS = "exists"
    STATE_ENFORCED = "enforced"
    STATE_PRESENT = "present"

    tmp_file = None

    def __init__(self, module, params=None, **kwargs):
        self.api_endpoint = kwargs.get('api_endpoint', self.API_ENDPOINT_NAME)
        self.data = None
        self.module = module
        self.new_fields = dict()
        self.params = params if params else module.params
        self.state = self.params.get('state', self.STATE_PRESENT)

    @abstractmethod
    def unique_field(self):
        pass

    @abstractmethod
    def set_new_fields(self):
        pass

    @classmethod
    def init_tmp_file(cls):
        if cls.tmp_file is None:
            cls.tmp_file = tempfile.NamedTemporaryFile(mode="w", prefix=f"gw_{cls.API_ENDPOINT_NAME}_", delete=False)

    def manage(self, auto_exit=True, fail_when_not_exists=True, **kwargs):
        self.get_existing_item()

        # Just Check if exists
        if self.exists():
            if self.data is None:
                if fail_when_not_exists:
                    self.module.fail_json(msg=f"Item {self.ITEM_TYPE} does not exist: {self.unique_value()}")
                else:
                    return

            self.module.json_output["id"] = self.data['id']
            if auto_exit:
                self.module.exit_json(**self.module.json_output)

        # Delete
        elif self.absent():
            self.module.delete_if_needed(self.data, auto_exit=auto_exit)

        # Create/Update
        elif self.present() or self.enforced():
            if self.enforced():
                self.new_fields = self.module.get_enforced_defaults(self.api_endpoint)[0]

            self.set_new_fields()

            self.data = self.module.create_or_update_if_needed(
                self.data, self.new_fields, endpoint=self.api_endpoint, item_type=self.ITEM_TYPE, auto_exit=False
            )
            for output_field in kwargs.get('json_output_fields', []):
                if output_field in self.data:
                    self.module.json_output[output_field] = self.data[output_field]

            if auto_exit:
                self.module.exit_json(**self.module.json_output)

    def get_existing_item(self):
        if self.data is None:
            self.data = self.module.get_one(self.api_endpoint, name_or_id=self.unique_value())

        return self.data

    def set_name_field(self):
        # Update
        name = self.module.params.get('new_name')
        if name is not None:
            self.new_fields['name'] = name
        # Get from existing item
        elif self.data is not None:
            self.new_fields['name'] = self.data.get('name')
        # Get from params
        elif self.module.params.get('name') is not None:
            self.new_fields['name'] = self.module.params.get('name')

    def unique_value(self):
        if self.params.get('id') is not None:
            return self.params.get('id')
        return self.params.get(self.unique_field())

    def exists(self):
        return self.state == self.STATE_EXISTS

    def present(self):
        return self.state == self.STATE_PRESENT

    def absent(self):
        return self.state == self.STATE_ABSENT

    def enforced(self):
        return self.state == self.STATE_ENFORCED

    def debug(self, msg):
        if not msg:
            return

        self.init_tmp_file()

        if isinstance(msg, dict):
            msg = json.dumps(msg)

        if msg[-1] != '\n':
            msg += '\n'

        self.tmp_file.write(msg)
