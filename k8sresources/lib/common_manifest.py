from cdk8s import ApiObjectMetadata
from cdk8s_plus_17 import Deployment, ContainerProps, Service, ServicePort, ConfigMap, Secret
from constructs import Construct
from k8sresources.imports import k8s
from k8sresources.imports.io.cert_manager import ClusterIssuer, ClusterIssuerSpec, ClusterIssuerSpecAcme, \
    ClusterIssuerSpecAcmePrivateKeySecretRef, ClusterIssuerSpecAcmeSolvers, ClusterIssuerSpecAcmeSolversHttp01, \
    ClusterIssuerSpecAcmeSolversHttp01Ingress, Certificate, CertificateSpec, CertificateSpecIssuerRef

from k8sresources.imports.k8s import ObjectMeta


class ApplicationNamespace(Construct):
    def __init__(self, scope: "Construct", id: str, *, namespace: str):
        # Namespace
        super().__init__(scope, id)
        namespace = k8s.KubeNamespace(self, namespace, metadata=ObjectMeta(name=namespace))
        self.namespace = namespace.name


class ApplicationDeployment(Construct):
    def __init__(self, scope: Construct, id: str, *, image: str, replicas: int, namespace: str,
                 issuer_ref_name: str = 'letsencrypt-staging', port: int = 80, target_port: int = 8080,
                 label: dict = None):
        super().__init__(scope, id)

        kplus_deployment = Deployment(self, 'deployment', replicas=replicas,
                                      metadata=ApiObjectMetadata(labels=label, namespace=namespace),
                                      pod_metadata=ApiObjectMetadata(labels=label),
                                      default_selector=True,
                                      containers=[ContainerProps(name=id,
                                                                 image=image, port=target_port)])
        kplus_deployment.metadata.add_label('namespace', namespace)
        # Service
        hello_service = Service(self, 'service', ports=[ServicePort(port=port, target_port=target_port)],
                                metadata=ApiObjectMetadata(namespace=namespace))
        hello_service.add_selector(label='app', value=kplus_deployment.metadata.get_label('app'))
        hello_service.metadata.add_label('namespace', namespace)

        self.service_name = hello_service.name
        self.service_port = port


class IngressAndCertificate(Construct):
    def __init__(self, scope: Construct, id: str, *, service_name: str,
                 private_key_secret_ref: str, email: str,
                 cluster_issuer_server: str = 'https://acme-staging-v02.api.letsencrypt.org/directory',
                 secret_name: str, common_name: str, dns_names: [str], issuer_ref_name: str = 'letsencrypt-staging',
                 namespace: str, service_port: int = 80):
        super().__init__(scope, id)
        # Ingress
        service_port = k8s.IntOrString.from_number(service_port)
        backend = k8s.IngressBackend(service_name=service_name, service_port=service_port)
        paths = k8s.HttpIngressPath(backend=backend, path='/')
        ingress_rule_value = k8s.HttpIngressRuleValue(paths=[paths])
        rules = k8s.IngressRule(host=dns_names[0], http=ingress_rule_value)
        tls = k8s.IngressTls(secret_name=secret_name,
                             hosts=dns_names)
        specs = k8s.IngressSpec(backend=backend, rules=[rules], tls=[tls])
        ingress = k8s.KubeIngressV1Beta1(self, '{0}-ingress'.format(id),
                                         metadata=ObjectMeta(name='{0}-ingress'.format(id), namespace=namespace,
                                                             annotations={
                                                                 "kubernetes.io/ingress.class": "traefik",
                                                                 "cert-manager.io/cluster-issuer": issuer_ref_name}),
                                         spec=specs)

        # Certificates and Issuer
        cluster_issuer = ClusterIssuer(self, 'clusterIssuer', spec=ClusterIssuerSpec(acme=ClusterIssuerSpecAcme(
            private_key_secret_ref=ClusterIssuerSpecAcmePrivateKeySecretRef(name=private_key_secret_ref),
            server=cluster_issuer_server, email=email,
            solvers=[ClusterIssuerSpecAcmeSolvers(http01=ClusterIssuerSpecAcmeSolversHttp01(
                ingress=ClusterIssuerSpecAcmeSolversHttp01Ingress(class_='traefik')))])),
                                       metadata={'name': issuer_ref_name})
        certificate = Certificate(self, 'certificate',
                                  metadata={'name': secret_name, 'namespace': namespace},
                                  spec=CertificateSpec(secret_name=secret_name,
                                                       common_name=common_name,
                                                       dns_names=dns_names,
                                                       issuer_ref=CertificateSpecIssuerRef(name=issuer_ref_name,
                                                                                           kind='ClusterIssuer')))


class ApplicationConfigMap(Construct):
    def __init__(self, scope: Construct, id: str, *,
                 namespace: str, file: str = None, **kwargs):
        super().__init__(scope, id)

        config_map = ConfigMap(self, 'config_map',
                               metadata=ApiObjectMetadata(name='application-config-map', namespace=namespace))
        for (k, v) in kwargs.items():
            config_map.add_data(k, v)
        if file is not None:
            config_map.add_file(file)


class ApplicationSecrets(Construct):
    def __init__(self, scope: Construct, id: str, *,
                 namespace: str, **kwargs):
        super().__init__(scope, id)

        secret = Secret(self, 'app_secret',
                        metadata=ApiObjectMetadata(name='application-secret', namespace=namespace))
        for (k, v) in kwargs.items():
            secret.add_string_data(k, v)
