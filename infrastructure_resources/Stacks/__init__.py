import os

from Crypto.PublicKey import RSA
from cdktf import App
from decouple import config

from . import common_stack
from . import k8s_stack
from . import virtual_machine_stack


class CreateK8Stack:
    def __init__(self):
        super().__init__()

    __code_dir_prifix = 'generated_code'
    key = RSA.generate(4096, os.urandom)
    with open(os.path.join("../stack-vm2.pem"), 'wb') as content_file:
        content_file.write(key.exportKey('PEM'))
        key_data = str(key.publickey().exportKey('OpenSSH').decode("utf-8"))

    auth_dict = {"subscription_id": config('subscription_id'), "client_id": config('client_id'),
                 "client_secret": config('client_secret'), "tenant_id": config('tenant_id'),
                 "access_key": config('access_key'), "key_data": key_data}

    def create_stack(self):
        app_common = App(context={'stack': 'common_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'common'),
                         stack_traces=False)
        app_vm = App(context={'stack': 'virtual_machine_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'vm'),
                     stack_traces=False)
        app_k8s = App(context={'stack': 'k8s_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'k8s'),
                      stack_traces=False)
        common_stack.CommonStack(app_common, 'common_stack', self.auth_dict)
        app_common.synth()
        virtual_machine_stack.VirtualMachineStack(app_vm, "virtual-machine", self.auth_dict)
        app_vm.synth()
        k8s_stack_variable = {'tags': {'foo': 'bar'}, 'rg_name': 'k8s_rg', 'vm_size': 'Standard_D2_v2',
                              'dns_prefix': 'k8s', 'common_code_dir': 'common'.format(self.__code_dir_prifix)}
        k8s_stack.K8Stack(app_k8s, "k8s-cluster", auth_dict=self.auth_dict, k8s_stack_variable=k8s_stack_variable)
        app_k8s.synth()
        return "success"
