#!/usr/bin/env python
from cdk8s import App, Chart, ApiObjectMetadata
from cdk8s_plus_17 import Deployment, ContainerProps, Service, ServicePort
from constructs import Construct

from k8sresources.imports import k8s
from k8sresources.imports.cert_manager.io.certificate import Certificate, CertificateSpec, CertificateSpecIssuerRef
from k8sresources.imports.cert_manager.io.clusterissuer import ClusterIssuer, ClusterIssuerSpec, ClusterIssuerSpecAcme, \
    ClusterIssuerSpecAcmePrivateKeySecretRef, ClusterIssuerSpecAcmeSolvers, ClusterIssuerSpecAcmeSolversHttp01, \
    ClusterIssuerSpecAcmeSolversHttp01Ingress
from k8sresources.imports.k8s import ObjectMeta, NamespaceSpec


class MyChart(Chart):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        # define resources here

        label = {"app": "hello-k8s"}
        namespace = k8s.KubeNamespace(self, 'prateek-test',metadata=ObjectMeta(name='prateek-test'))
        kplus_deployment = Deployment(self, 'deployment', replicas=2, metadata=ApiObjectMetadata(labels=label),
                                      pod_metadata=ApiObjectMetadata(labels=label),
                                      default_selector=True,
                                      containers=[ContainerProps(name='hello-kubernetes',
                                                                 image='paulbouwer/hello-kubernetes:1.7', port=8080)])
        kplus_deployment.metadata.add_label('namespace', namespace.name)
        hello_service = Service(self, 'service', ports=[ServicePort(port=80, target_port=8080)])
        hello_service.add_selector(label='app', value=kplus_deployment.pod_metadata.get_label('app'))
        hello_service.metadata.add_label('namespace', namespace.name)

        #        ingress = IngressV1Beta1(self,'ingress')
        #        ingress.add_rule(path='/hello', backend=IngressV1Beta1Backend.from_service(hello_service,port=82))
        #        ingress.add_host_default_backend(host='prateek-traefik.westeurope.cloudapp.azure.com',backend=IngressV1Beta1Backend.from_service(hello_service))

        service_port = k8s.IntOrString.from_number(80)
        backend = k8s.IngressBackend(service_name=hello_service.name, service_port=service_port)
        paths = k8s.HttpIngressPath(backend=backend, path='/')
        ingress_rule_value = k8s.HttpIngressRuleValue(paths=[paths])
        rules = k8s.IngressRule(host='prateek-traefik.westeurope.cloudapp.azure.com', http=ingress_rule_value)
        tls = k8s.IngressTls(secret_name='prateek-traefik-cert',
                             hosts=['prateek-traefik.westeurope.cloudapp.azure.com'])
        specs = k8s.IngressSpec(backend=backend, rules=[rules], tls=[tls])
        ingress = k8s.KubeIngressV1Beta1(self, 'hello-ingress', metadata=ObjectMeta(name='hello-ingress', annotations={
            "kubernetes.io/ingress.class": "traefik",
            "cert-manager.io/cluster-issuer": "letsencrypt-staging"}), spec=specs)
        cluster_issuer = ClusterIssuer(self, 'clusterIssuer', spec=ClusterIssuerSpec(acme=ClusterIssuerSpecAcme(
            private_key_secret_ref=ClusterIssuerSpecAcmePrivateKeySecretRef(name='prateek-cert'),
            server='https://acme-staging-v02.api.letsencrypt.org/directory', email='prateek1411@gmail.com',
            solvers=[ClusterIssuerSpecAcmeSolvers(http01=ClusterIssuerSpecAcmeSolversHttp01(
                ingress=ClusterIssuerSpecAcmeSolversHttp01Ingress(class_='traefik')))])),
                                       metadata={'name': 'letsencrypt-staging'})
        certificate = Certificate(self, 'certificate',
                                  metadata={'name': 'prateek-traefik-cert', 'namespace': 'prateek-test'},
                                  spec=CertificateSpec(secret_name='prateek-traefik-cert',
                                                       common_name='prateek-traefik.westeurope.cloudapp.azure.com',
                                                       dns_names=['prateek-traefik.westeurope.cloudapp.azure.com'],
                                                       issuer_ref=CertificateSpecIssuerRef(name='letsencrypt-staging',
                                                                                           kind='ClusterIssuer')))


app = App()
MyChart(app, "k8sresources")

app.synth()
