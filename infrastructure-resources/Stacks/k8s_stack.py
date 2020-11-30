from cdktf import TerraformResourceLifecycle, TerraformStack, AzurermBackend, TerraformVariable
from constructs import Construct

from Stacks.utils import check_keys
from imports.azurerm import KubernetesClusterNodePool, KubernetesClusterRoleBasedAccessControl, \
    KubernetesClusterAddonProfileKubeDashboard, KubernetesClusterDefaultNodePool, ResourceGroup, \
    KubernetesClusterIdentity, KubernetesClusterLinuxProfile, KubernetesClusterLinuxProfileSshKey, KubernetesCluster, \
    KubernetesClusterNetworkProfile, KubernetesClusterAddonProfile, AzurermProviderFeatures, AzurermProvider


class MyK8S(TerraformStack):
    def __init__(self, scope: Construct, ns: str, auth_dict: dict, k8s_stack_variable: dict):
        keys = list(auth_dict.keys())
        subscription_id = auth_dict['subscription_id'] if check_keys(key='subscription_id',
                                                                     key_list=keys) else None
        client_id = auth_dict['client_id'] if check_keys(key='client_id', key_list=keys) else None
        client_secret = auth_dict['client_secret'] if check_keys(key='client_secret', key_list=keys) else None
        tenant_id = auth_dict['tenant_id'] if check_keys(key='tenant_id', key_list=keys) else None
        access_key = auth_dict['access_key'] if check_keys(key='access_key', key_list=keys) else None
        key_data = auth_dict['key_data'] if check_keys(key='key_data', key_list=keys) else None

        ######### App Variables###########
        keys = list(k8s_stack_variable.keys())
        var_tags = k8s_stack_variable['tags'] if check_keys(key='tags', key_list=keys) else None
        var_rg_name = k8s_stack_variable['rg_name'] if check_keys(key='rg_name', key_list=keys) else None
        var_vm_size = k8s_stack_variable['vm_size'] if check_keys(key='vm_size', key_list=keys) else None
        super().__init__(scope, ns)
        ##### Terraform Variables ########

        tf_key_data = TerraformVariable(self, 'key_data', type='string', default=key_data)
        tf_access_key = TerraformVariable(self, 'access_key', type='string', default=access_key)
        tf_location = TerraformVariable(self, 'location', type='string', default='East Us')

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

        backend = AzurermBackend(self, resource_group_name=tf_resource_group_name.string_value,
                                 storage_account_name=tf_storage_account_name.string_value,
                                 container_name=tf_container_name.string_value, key=tf_storage_tfstate_key.string_value,
                                 access_key=tf_access_key.string_value)
        features = AzurermProviderFeatures()

        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id,
                                   client_id=client_id, client_secret=client_secret,
                                   tenant_id=tenant_id)
        node_pool = KubernetesClusterDefaultNodePool(
            name='default', node_count=1, vm_size=var_vm_size)

        # resource_group = ResourceGroupConfig(name='test', location='East US')
        resource_group = ResourceGroup(self, 'azure-rg', name='k8s_rg', location=tf_location.string_value)

        identity = KubernetesClusterIdentity(type='SystemAssigned')
        linux_profile = KubernetesClusterLinuxProfile(admin_username='ubuntu',
                                                      ssh_key=[KubernetesClusterLinuxProfileSshKey(
                                                          key_data=tf_key_data.string_value)])

        cluster = KubernetesCluster(
            self, 'my-kube-cluster',
            name='my-kube-cluster',
            default_node_pool=[node_pool],
            dns_prefix='k8s',
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
        cluster_node_pool = KubernetesClusterNodePool(
            self, "k8sNodePool",
            kubernetes_cluster_id=cluster.id,
            name='k8snodepool', node_count=1, vm_size=var_vm_size,
            enable_auto_scaling=True,
            min_count=1, max_count=2, max_pods=10,
            lifecycle=TerraformResourceLifecycle(create_before_destroy=True, ignore_changes=['node_count']))
