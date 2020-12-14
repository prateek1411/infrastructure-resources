from cdktf import TerraformVariable, TerraformModule, TerraformOutput
from constructs import Construct

from Stacks.backend import TerraformStackWithBackend
from utils import check_keys, add_base64decode
from imports.azurerm import KubernetesClusterRoleBasedAccessControl, \
    KubernetesClusterAddonProfileKubeDashboard, KubernetesClusterDefaultNodePool, ResourceGroup, \
    KubernetesClusterIdentity, KubernetesClusterLinuxProfile, KubernetesClusterLinuxProfileSshKey, KubernetesCluster, \
    KubernetesClusterNetworkProfile, KubernetesClusterAddonProfile, AzurermProviderFeatures, AzurermProvider
from imports.kubernetes import KubernetesProvider, Namespace, NamespaceMetadata

from imports.helm import HelmProvider, HelmProviderKubernetes, Release

from imports.local import File


class K8Stack(TerraformStackWithBackend):
    def __init__(self, scope: Construct, ns: str, auth_dict: dict, k8s_stack_variable: dict):
        keys = list(auth_dict.keys())

        access_key = auth_dict['access_key'] if check_keys(key='access_key', key_list=keys) else None
        key_data = auth_dict['key_data'] if check_keys(key='key_data', key_list=keys) else None
        subscription_id = auth_dict['subscription_id'] if check_keys(key='subscription_id',
                                                                     key_list=keys) else None
        client_id = auth_dict['client_id'] if check_keys(key='client_id', key_list=keys) else None
        client_secret = auth_dict['client_secret'] if check_keys(key='client_secret', key_list=keys) else None
        tenant_id = auth_dict['tenant_id'] if check_keys(key='tenant_id', key_list=keys) else None
        ######### App Variables###########
        keys = list(k8s_stack_variable.keys())
        var_tags = k8s_stack_variable['tags'] if check_keys(key='tags', key_list=keys) else None
        var_rg_name = k8s_stack_variable['rg_name'] if check_keys(key='rg_name', key_list=keys) else None
        var_vm_size = k8s_stack_variable['vm_size'] if check_keys(key='vm_size', key_list=keys) else None
        var_dns_prefix = k8s_stack_variable['dns_prefix'] if check_keys(key='dns_prefix', key_list=keys) else None
        common_code_dir = k8s_stack_variable['common_code_dir'] if check_keys(key='common_code_dir',
                                                                              key_list=keys) else None
        super().__init__(scope, ns)
        ##### Terraform Variables ########

        tf_key_data = TerraformVariable(self, 'key_data', type='string', default=key_data)
        tf_access_key = TerraformVariable(self, 'access_key', type='string', default=access_key)
        tf_location = TerraformVariable(self, 'location', type='string', default='West Europe')

        tf_storage_resource_group_name = TerraformVariable(self, 'stogage_resource_group_name', type='string',
                                                           default='prateek-vm_group')

        tf_resource_group_name = TerraformVariable(self, 'resource_group_name', type='string',
                                                   default=var_rg_name)

        tf_storage_account_name = TerraformVariable(self, 'storage_account_name', type='string',
                                                    default='digirisestatic')
        tf_container_name = TerraformVariable(self, 'container_name', type='string',
                                              default='tfstate')

        tf_storage_tfstate_key = TerraformVariable(self, 'storage_tfstate_key', type='string',
                                                   default='prod.terraform.tfstate.prateek-vm2')
        tf_node_count = TerraformVariable(self, 'node_count', type='number',
                                          default=1)
        tf_min_count = TerraformVariable(self, 'min_count', type='number',
                                         default=1)
        tf_max_count = TerraformVariable(self, 'max_count', type='number',
                                         default=2)
        tf_max_pod = TerraformVariable(self, 'max_pod', type='number',
                                       default=20)
        features = AzurermProviderFeatures()

        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id,
                                   client_id=client_id, client_secret=client_secret,
                                   tenant_id=tenant_id)

        common_module = TerraformModule(self, 'common_module', source='../{0}'.format(common_code_dir))
        node_pool = KubernetesClusterDefaultNodePool(
            name='default', node_count=tf_node_count.number_value, vm_size=var_vm_size)

        # resource_group = ResourceGroupConfig(name='test', location='East US')
        resource_group = ResourceGroup(self, 'azure-rg', name=var_rg_name, location=tf_location.string_value)

        identity = KubernetesClusterIdentity(type='SystemAssigned')

        linux_profile = KubernetesClusterLinuxProfile(admin_username='ubuntu',
                                                      ssh_key=[KubernetesClusterLinuxProfileSshKey(
                                                          key_data=tf_key_data.string_value)])

        cluster = KubernetesCluster(
            self, 'my-kube-cluster',
            name='my-kube-cluster',
            default_node_pool=[node_pool],
            dns_prefix=var_dns_prefix,
            location=resource_group.location,
            resource_group_name=resource_group.name,
            identity=[identity],
            linux_profile=[linux_profile],
            network_profile=[KubernetesClusterNetworkProfile(network_plugin='azure')],
            addon_profile=[
                KubernetesClusterAddonProfile(
                    kube_dashboard=[KubernetesClusterAddonProfileKubeDashboard(enabled=True)],
                    #                   oms_agent=[KubernetesClusterAddonProfileOmsAgent(enabled=True,log_analytics_workspace_id='test')]
                )
            ],
            role_based_access_control=[KubernetesClusterRoleBasedAccessControl(enabled=True)],
            tags=var_tags
        )
        kube_config = cluster.kube_config_raw
        File(filename=os.path.join(path.join(self.__code_dir_prifix, 'generated_files'), content_base64=kube_config))
        TerraformOutput(self, 'kube_config', value=kube_config, sensitive=True)
        #        cluster_node_pool = KubernetesClusterNodePool(
        #            self, "k8sNodePool",
        #            kubernetes_cluster_id=cluster.id,
        #            name='k8snodepool', node_count=tf_node_count.number_value, vm_size=var_vm_size,
        #            enable_auto_scaling=True,
        #            min_count=tf_min_count.number_value, max_count=tf_max_count.number_value, max_pods=tf_max_pod.number_value,
        #            lifecycle=TerraformResourceLifecycle(create_before_destroy=True, ignore_changes=['node_count']))

        #        RoleAssignment(self, "network_contributer", scope=resource_group.id,
        #                       principal_id=identity.principal_id,
        #                       role_definition_name='Network Contributor')
        #        RoleAssignment(self, "kubectl_pull", scope=resource_group.id,
        #                       principal_id=cluster.kubelet_identity(index='0').object_id,
        #                       role_definition_name='AcrPull')
        #
        ###############Removed Temporarly ######################################
        k8s_provider = KubernetesProvider(self, 'k8s', load_config_file=False,
                                          host=cluster.kube_config(index='0').host,
                                          client_key=add_base64decode(cluster.kube_config(index='0').client_key),
                                          client_certificate=add_base64decode(
                                              cluster.kube_config(index='0').client_certificate),
                                          cluster_ca_certificate=add_base64decode(
                                              cluster.kube_config(index='0').cluster_ca_certificate)
                                          )

        helm_provider = HelmProvider(self, 'helm', kubernetes=[HelmProviderKubernetes(load_config_file=False,
                                                                                      host=cluster.kube_config(
                                                                                          index='0').host,
                                                                                      client_key=add_base64decode(
                                                                                          cluster.kube_config(
                                                                                              index='0').client_key),
                                                                                      client_certificate=add_base64decode(
                                                                                          cluster.kube_config(
                                                                                              index='0').client_certificate),
                                                                                      cluster_ca_certificate=add_base64decode(
                                                                                          cluster.kube_config(
                                                                                              index='0').cluster_ca_certificate))])

        # Add traefik and certmanager to expose services by https.
        traefik_ns_metadata = NamespaceMetadata(name='traefik', labels={'created_by': 'PythonCDK', 'location': 'eastus',
                                                                        'resource_group': var_rg_name})
        traefik_ns = Namespace(self, 'traefik-ns', metadata=[traefik_ns_metadata])
        helm_traefik2_value = '''
additionalArguments:
  - "--entrypoints.websecure.http.tls"
  - "--providers.kubernetesingress=true"
  - "--providers.kubernetesIngress.ingressClass=traefik"
  - "--ping"
  - "--metrics.prometheus"
'''
        helm_traefik2_release = Release(self, 'traefik2', name='traefik',
                                        repository='https://containous.github.io/traefik-helm-chart',
                                        chart='traefik', namespace='traefik',
                                        values=[helm_traefik2_value])

        cert_manager_ns_metadata = NamespaceMetadata(name='cert-manager',
                                                     labels={'created_by': 'PythonCDK', "location": 'westeurope',
                                                             'resource_group': var_rg_name})
        cert_manager_ns = Namespace(self, 'cert-manager-ns', metadata=[cert_manager_ns_metadata], )

        cert_manager_value = '''
 ingressShim:
     defaultIssuerKind: ClusterIssuer
     defaultIssuerName: letsencrypt-prod
     installCRDs: true
 '''
        cert_manager_release = Release(self, 'cert-manager', name='cert-manager',
                                       repository='https://charts.jetstack.io',
                                       chart='cert-manager', namespace='cert-manager',
                                       values=[cert_manager_value]
                                       )
