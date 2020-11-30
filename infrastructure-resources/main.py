import os

from Crypto.PublicKey import RSA
from cdktf import App, TerraformVariable
from decouple import config

from Stacks import k8s_stack, virtual_machine_stack

key = RSA.generate(4086, os.urandom)
with open(os.path.join("../Prateek-vm2.pem"), 'wb') as content_file:
    content_file.write(key.exportKey('PEM'))
    key_data = str(key.publickey().exportKey('OpenSSH').decode("utf-8"))

auth_dict = {"subscription_id": config('subscription_id'), "client_id": config('client_id'),
             "client_secret": config('client_secret'), "tenant_id": config('tenant_id'),
             "access_key": config('access_key'), "key_data": key_data}

k8s_stack_variable = {'tags': {'foo': 'bar'}, 'rg_name': 'k8s_rg','vm_size': 'Standard_D2_v2'}
app_vm = App(outdir='vm', stack_traces=False)
app_k8s = App(outdir='k8s', stack_traces=False)
# virtual_machine_stack.MyVirtualMachine(app_vm, "virtual-machine", auth_dict)
k8s_stack.MyK8S(app_k8s, "k8s-cluster", auth_dict=auth_dict, k8s_stack_variable=k8s_stack_variable)
app_k8s.synth()
# app_vm.synth()
