import os
import yaml

from cdk8s import App, Chart
from constructs import Construct

from k8sresources.lib.utils import ApplicationOptions
from k8sresources.lib.common_manifest import IngressAndCertificate, ApplicationDeployment, ApplicationConfigMap, \
    ApplicationNamespace


class HelloApplication(Chart):
    def __init__(self, scope: Construct, ns: str, deployment_variables: str = None, dict_values: dict = None):
        super().__init__(scope, ns)
        # file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','.env')
        # values = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../values.yaml')
        if type(deployment_variables).__name__ == 'dict':
            try:
                dict_values = deployment_variables['application']
            except KeyError as key_err:
                print('Application Configurations not found')
                exit(1)
        else:
            if deployment_variables is not None:
                if os.path.isfile(deployment_variables):
                    if os.path.splitext(deployment_variables)[-1].lower() in ('.yaml', '.yml'):
                        with open(deployment_variables, mode='r') as values_yaml:
                            try:
                                dict_values = yaml.full_load(values_yaml)['application']
                            except KeyError as key_err:
                                print('Application Configurations not found')
                                exit(1)
                    else:
                        print("please provide yaml or yml file")
                #       print(dict_values)

        if dict_values is None:
            print('Please provide Input Usage: ...')
            exit(1)
        try:
            options = ApplicationOptions(dict_values)

            app_namespace = ApplicationNamespace(self, 'namespace', namespace=options.namespace)
            configmap = ApplicationConfigMap(self, 'config-map', namespace=app_namespace.namespace)

            application = ApplicationDeployment(self, "application",
                                                image=options.image,
                                                replicas=options.replicas, namespace=app_namespace.namespace,
                                                label=options.lable)
            certificate = IngressAndCertificate(self, "certificate", service_name=application.service_name,
                                                service_port=application.service_port,
                                                secret_name=options.secret_name,
                                                common_name=options.common_name,
                                                dns_names=options.dns_names,
                                                namespace=app_namespace.namespace,
                                                private_key_secret_ref=options.private_key_secret_ref,
                                                email=options.email)
        except KeyError as err:
            print('{0} is required'.format(err.__str__()))
            exit(1)


class CreateChart:
    def __init__(self, deployment_id: str, blueprint_id):
        self.deployment_id = deployment_id
        self.blueprint_id = blueprint_id
        self.__code_dir_prefix= None

    def create_chart(self, *, gen_code_dir, values):
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
        app = App(outdir=os.path.join(self.__code_dir_prefix, 'kubectl_manifest'))
        HelloApplication(app, 'k8sresources', deployment_variables=values)
        app.synth()
