#!/usr/bin/env python
from cdktf import App, TerraformStack
from constructs import Construct
from decouple import config
import os

from imports.azurerm import (AzurermProvider, AzurermProviderFeatures,
                             KubernetesCluster,
                             KubernetesClusterDefaultNodePool,
                             KubernetesClusterIdentity, ResourceGroupConfig)


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # define resources here
        subscription_id=config('subscription_id')
        client_id=config('client_id')
        client_secret=config('client_secret')
        tenant_id=config('tenant_id')
        features = AzurermProviderFeatures()
        provider = AzurermProvider(self, 'azure', features=[features], subscription_id=subscription_id, client_id=client_id, client_secret=client_secret,
            tenant_id=tenant_id)

        node_pool = KubernetesClusterDefaultNodePool(
           name='default', node_count=1, vm_size='Standard_D2_v2')

        resource_group = ResourceGroupConfig(name='OUR_RESOURCE_GROUP', location='East US')

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
app = App()
MyStack(app, "infrastructure-resources")

app.synth()
