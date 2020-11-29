import os

from Crypto.PublicKey import RSA
from cdktf import TerraformResourceLifecycle, TerraformStack
from constructs import Construct
from decouple import config

from imports.azurerm import KubernetesClusterNodePool, KubernetesClusterRoleBasedAccessControl, \
    KubernetesClusterAddonProfileKubeDashboard, KubernetesClusterDefaultNodePool, ResourceGroup, \
    KubernetesClusterIdentity, KubernetesClusterLinuxProfile, KubernetesClusterLinuxProfileSshKey, KubernetesCluster, \
    KubernetesClusterNetworkProfile, KubernetesClusterAddonProfile

subscription_id = config('subscription_id')
client_id = config('client_id')
client_secret = config('client_secret')
tenant_id = config('tenant_id')
access_key = config('access_key')
key = RSA.generate(4086, os.urandom)
with open(os.path.join("../Prateek-vm2.pem"), 'wb') as content_file:
    content_file.write(key.exportKey('PEM'))
    key_data = str(key.publickey().exportKey('OpenSSH').decode("utf-8"))


class MyK8S(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        node_pool = KubernetesClusterDefaultNodePool(
            name='default', node_count=1, vm_size='Standard_D2_v2')

        # resource_group = ResourceGroupConfig(name='test', location='East US')
        resource_group = ResourceGroup(self, 'azure-rg', name='test', location='East US')

        identity = KubernetesClusterIdentity(type='SystemAssigned')
        linux_profile = KubernetesClusterLinuxProfile(admin_username='ubuntu',
                                                      ssh_key=[KubernetesClusterLinuxProfileSshKey(key_data=key_data)])

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
            tags={"foo": "bar"}
        )
        cluster_node_pool = KubernetesClusterNodePool(
            self, "k8sNodePool",
            kubernetes_cluster_id=cluster.id,
            name='k8snodepool', node_count=1, vm_size='Standard_D2_v2',
            enable_auto_scaling=True,
            min_count=1, max_count=2, max_pods=10,
            lifecycle=TerraformResourceLifecycle(create_before_destroy=True, ignore_changes=['node_count']))
