from constructs import Construct
from infrastructure_resources.imports.azurerm import AzurermProviderFeatures, AzurermProvider, ResourceGroup

from infrastructure_resources.Stacks.backend import TerraformStackWithBackend
from utils import check_keys


class CommonStack(TerraformStackWithBackend):
    def __init__(self, scope: Construct, ns: str, *, auth_dict: dict):
        keys = list(auth_dict.keys())
        subscription_id = auth_dict['subscription_id'] if check_keys(key='subscription_id',
                                                                     key_list=keys) else None
        client_id = auth_dict['client_id'] if check_keys(key='client_id', key_list=keys) else None
        client_secret = auth_dict['client_secret'] if check_keys(key='client_secret', key_list=keys) else None
        tenant_id = auth_dict['tenant_id'] if check_keys(key='tenant_id', key_list=keys) else None
        access_key = auth_dict['access_key'] if check_keys(key='access_key', key_list=keys) else None
        key_data = auth_dict['key_data'] if check_keys(key='key_data', key_list=keys) else None

        super().__init__(scope, ns)

        # define resources here
        backend = super().backend
        features = AzurermProviderFeatures()

        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id,
                                   client_id=client_id, client_secret=client_secret,
                                   tenant_id=tenant_id)

        resource_group = ResourceGroup(self, 'azurerg', name='common', location='East US')
