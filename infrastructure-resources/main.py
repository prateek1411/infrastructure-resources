import os

from cdktf import App, TerraformStack, AzurermBackend
from constructs import Construct
from decouple import config
from Crypto.PublicKey import RSA

from imports.azurerm import (AzurermProvider, AzurermProviderFeatures,
                             KubernetesCluster,
                             KubernetesClusterDefaultNodePool,
                             KubernetesClusterIdentity, VirtualNetwork,
                             SubnetA, ResourceGroup, NetworkInterfaceA, NetworkInterfaceIpConfiguration,
                             VirtualMachine, VirtualMachineStorageOsDisk, ImageConfig,
                             VirtualMachineStorageImageReference, VirtualMachineOsProfile,
                             VirtualMachineOsProfileLinuxConfig, VirtualMachineOsProfileLinuxConfigSshKeys,
                             ResourceGroupConfig)

subscription_id = config('subscription_id')
client_id = config('client_id')
client_secret = config('client_secret')
tenant_id = config('tenant_id')
access_key = config('access_key')


class MyVirtualMachine(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # define resources here

        backend = AzurermBackend(self, resource_group_name='prateek-vm_group', storage_account_name='digirisestatic',
                                 container_name='tfstate', key="prod.terraform.tfstate.prateek-vm2",
                                 access_key=access_key)
        features = AzurermProviderFeatures()

        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id,
                                   client_id=client_id, client_secret=client_secret,
                                   tenant_id=tenant_id)

        node_pool = KubernetesClusterDefaultNodePool(
            name='default', node_count=1, vm_size='Standard_D2_v2')

        resource_group = ResourceGroup(self, 'azure-rg', name='test', location='East US')

        identity = KubernetesClusterIdentity(type='SystemAssigned')

        virtual_network = VirtualNetwork(self, 'azure-net', name='TerraformVNet',
                                         location='East US',
                                         address_space=['10.0.0.0/16'],
                                         resource_group_name=resource_group.name,
                                         depends_on=[resource_group]
                                         )
        virtual_subnetwork = SubnetA(self, 'azure-subnet', name='TerraformSubVNet',
                                     resource_group_name=resource_group.name,
                                     virtual_network_name=virtual_network.name,
                                     address_prefixs='10.0.0.0/24',
                                     depends_on=[resource_group, virtual_network]
                                     )
        ip_configuration = NetworkInterfaceIpConfiguration(name='private_ip',
                                                           private_ip_address_allocation='Dynamic',
                                                           subnet_id=virtual_subnetwork.id)
        v_nic = NetworkInterfaceA(self, 'azure-vnet', name='vNic', location='East US',
                                  ip_configuration=[ip_configuration],
                                  resource_group_name=resource_group.name,
                                  depends_on=[resource_group])
        storage_disk = VirtualMachineStorageOsDisk(name='azure_os_disk', create_option='FromImage', disk_size_gb=50)
        storage_image_ref = VirtualMachineStorageImageReference(offer='UbuntuServer', publisher='Canonical',
                                                                sku='18.04-LTS', version='latest')
        os_profile = VirtualMachineOsProfile(admin_username='prateek', computer_name='prateek-vm2')
        key = RSA.generate(4086, os.urandom)
        with open(os.path.join("Prateek-vm2.pem"), 'wb') as content_file:
            content_file.write(key.exportKey('PEM'))
            key_data = str(key.publickey().exportKey('OpenSSH').decode("utf-8"))
            print(key_data)
        ssh_keys = VirtualMachineOsProfileLinuxConfigSshKeys(
            path='/home/{0}/.ssh/authorized_keys'.format(os_profile.admin_username), key_data=key_data)
        os_profile_linux_config = VirtualMachineOsProfileLinuxConfig(disable_password_authentication=True,
                                                                     ssh_keys=[ssh_keys])
        azure_vm = VirtualMachine(self, 'azure_vm',
                                  location='East US',
                                  name='Prateek-vm2',
                                  network_interface_ids=[v_nic.id],
                                  resource_group_name=resource_group.name,
                                  storage_os_disk=[storage_disk],
                                  storage_image_reference=[storage_image_ref],
                                  os_profile=[os_profile],  #
                                  os_profile_linux_config=[os_profile_linux_config],
                                  vm_size='Standard_D2_v2')
        # cluster = KubernetesCluster(
        #    self, 'our-kube-cluster',
        #    name='our-kube-cluster',
        #    default_node_pool=[node_pool],
        #    dns_prefix='test',
        #    location=resource_group.location,
        #    resource_group_name=resource_group.name,
        #    depends_on=[resource_group],
        #    identity=[identity],
        #    tags={"foo": "bar"}
        # )
        #


class MyK8S(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        backend = AzurermBackend(self, resource_group_name='prateek-vm_group', storage_account_name='digirisestatic',
                                 container_name='tfstate', key="prod.terraform.tfstate.k8s",
                                 access_key=access_key)
        features = AzurermProviderFeatures()
        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id,
                                   client_id=client_id, client_secret=client_secret,
                                   tenant_id=tenant_id)

        node_pool = KubernetesClusterDefaultNodePool(
            name='default', node_count=1, vm_size='Standard_D2_v2')

        resource_group = ResourceGroupConfig(name='test', location='East US')

        identity = KubernetesClusterIdentity(type='SystemAssigned')

        cluster = KubernetesCluster(
            self, 'our-kube-cluster',
            name='our-kube-cluster',
            default_node_pool=[node_pool],
            dns_prefix='test',
            location=resource_group.location,
            resource_group_name=resource_group.name,
            identity=[identity],
            tags={"foo": "bar"}
        )


app_vm = App(outdir='vm', stack_traces=False)
app_k8s = App(outdir='k8s', stack_traces=False)
MyVirtualMachine(app_vm, "virtual-machine")
MyK8S(app_k8s, "k8s-cluster")
app_k8s.synth()
app_vm.synth()
