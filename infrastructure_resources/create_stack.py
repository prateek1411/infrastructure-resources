import os

import yaml
from Crypto.PublicKey import RSA
from cdktf import App
from decouple import config

from infrastructure_resources.Stacks import common_stack
from infrastructure_resources.Stacks import k8s_stack
from infrastructure_resources.Stacks import virtual_machine_stack


class CreateStack:
    def __init__(self, *, deployment_id: str, blueprint_id: str):
        self.__pem_file_name = '{0}.pem'.format(deployment_id)
        self.__code_dir_prefix = None
        self.deployment_id = deployment_id
        self.blueprint_id = blueprint_id

    def create_stack(self, *, gen_code_dir: str, auth_dict: dict, deployment_variables: str = None, dict_values: dict = None):
        self.__code_dir_prefix = os.path.join(gen_code_dir, self.blueprint_id, self.deployment_id)
        if not os.path.isdir(self.__code_dir_prefix):
            try:
                os.makedirs(self.__code_dir_prefix)
            except OSError:
                print("Creation of the directory %s failed" % self.__code_dir_prefix)
                exit(1)
            else:
                print("Successfully created the directory %s" % self.__code_dir_prefix)
        else:
            print("directory %s already exists" % self.__code_dir_prefix)

        if os.path.isfile(self.__pem_file_name):
            with open(os.path.join(self.__pem_file_name), 'r') as content_file:
                self.key_data = str(RSA.import_key(content_file.read()).exportKey('OpenSSH').decode('utf-8'))
        else:
            key = RSA.generate(4096, os.urandom)
            with open(os.path.join(self.__pem_file_name), 'wb') as content_file:
                content_file.write(key.exportKey('PEM'))
                self.key_data = str(key.publickey().exportKey('OpenSSH').decode('utf-8'))
        key = {"key_data": self.key_data}
        auth_dict1 = {**auth_dict, **key}
#        app_common = App(context={'stack': 'common_stack'}, outdir=os.path.join(self.__code_dir_prefix, 'common'),
#                         stack_traces=False)
#        app_vm = App(context={'stack': 'virtual_machine_stack'}, outdir=os.path.join(self.__code_dir_prefix, 'vm'),
#                     stack_traces=False)
        app_k8s = App(context={'stack': 'k8s_stack'}, outdir=os.path.join(self.__code_dir_prefix, 'k8s'),
                      stack_traces=False)
#        common_stack.CommonStack(app_common, 'common_stack', auth_dict=auth_dict1)
#        app_common.synth()
#        virtual_machine_stack.VirtualMachineStack(app_vm, "virtual-machine", auth_dict=auth_dict1)
#        app_vm.synth()
        if type(deployment_variables).__name__ == 'dict':
            try:
                dict_values = deployment_variables['terraform_inputs']
            except KeyError as key_err:
                print('Application Configurations not found')
                exit(1)
        else:
            if deployment_variables is not None:
                if os.path.isfile(deployment_variables):
                    if os.path.splitext(deployment_variables)[-1].lower() in ('.yaml', '.yml'):
                        with open(deployment_variables, mode='r') as values_yaml:
                            try:
                                dict_values = yaml.full_load(values_yaml)['terraform_inputs']
                            except KeyError as key_err:
                                print('Application Configurations not found')
                                exit(1)
                    else:
                        print("please provide yaml or yml file")
                #       print(dict_values)


        options = k8s_stack.OptionsK8Stack(dict_values)
        k8s_stack.K8Stack(app_k8s, "k8s-cluster", auth_dict=auth_dict1, k8s_stack_variable=options)
        app_k8s.synth()
        return "success"
