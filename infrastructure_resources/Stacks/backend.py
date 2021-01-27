from cdktf import TerraformStack, AzurermBackend
from constructs import Construct
from decouple import config


class TerraformStackWithBackend(TerraformStack):
    backend = None

    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        self.backend = AzurermBackend(self, resource_group_name='Prateek-Test',
                                      storage_account_name='terraformstateprateek',
                                      container_name='tfstate',
                                      key="prod.terraform.tfstate.{0}".format(self.__class__.__name__),
                                      access_key=config('access_key')
                                      )
