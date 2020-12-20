from constructs import ConstructOptions


class ApplicationOptions(ConstructOptions):
    def __init__(self,dict_values):
        super().__init__()
        try:
            self.namespace = dict_values['namespace']
            self.image = dict_values['image'] = "paulbouwer/hello-kubernetes:1.7"
            self.replicas = dict_values['replicas']
            self.lable = dict_values['lable']
            self.secret_name = dict_values['secret_name']
            self.common_name = dict_values['common_name']
            self.dns_names = dict_values['dns_names']
            self.private_key_secret_ref = dict_values['private_key_secret_ref']
            self.email = dict_values['email']
            self.configmap_values = dict_values['configmap_values']
        except KeyError as key_err:
            raise key_err
