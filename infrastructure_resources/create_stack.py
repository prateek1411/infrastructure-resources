import os

from Crypto.PublicKey import RSA
from cdktf import App
from decouple import config

import common_stack
import k8s_stack
import virtual_machine_stack


class CreateK8Stack():
    def __init__(self):
        super().__init__()

    __code_dir_prifix = 'generated_code'
    key = RSA.generate(4096, os.urandom)
    with open(os.path.join("stack-vm2.pem"), 'wb') as content_file:
        content_file.write(key.exportKey('PEM'))
        key_data = str(key.publickey().exportKey('OpenSSH').decode("utf-8"))



    def create_stack(self,auth_dict:dict):
        key = {"key_data": self.key_data}
        auth_dict1 = {**auth_dict , **key}
        app_common = App(context={'stack': 'common_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'common'),
                         stack_traces=False)
        app_vm = App(context={'stack': 'virtual_machine_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'vm'),
                     stack_traces=False)
        app_k8s = App(context={'stack': 'k8s_stack'}, outdir=os.path.join(self.__code_dir_prifix, 'k8s'),
                      stack_traces=False)
        common_stack.CommonStack(app_common, 'common_stack', auth_dict1)
        app_common.synth()
        virtual_machine_stack.VirtualMachineStack(app_vm, "virtual-machine", auth_dict1)
        app_vm.synth()
        k8s_stack_variable = {'tags': {'foo': 'bar'}, 'rg_name': 'k8s_rg', 'vm_size': 'Standard_B2s',
                              'dns_prefix': 'k8s', 'common_code_dir': 'common'.format(self.__code_dir_prifix)}
        k8s_stack.K8Stack(app_k8s, "k8s-cluster", auth_dict=auth_dict1, k8s_stack_variable=k8s_stack_variable)
        app_k8s.synth()
        return "success"
