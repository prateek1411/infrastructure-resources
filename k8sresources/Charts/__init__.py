#!/usr/bin/env python
import os

from cdk8s import App, Chart, ApiObjectMetadata
from .ingress_k8s import IngressAndCertManager


class K8SChart():
    def __init__(self):
        self.__code_dir_prifix = 'generated_code'

    def create_chart(self):
        app = App(outdir=os.path.join(self.__code_dir_prifix, 'kubectl_manifest'))
        IngressAndCertManager(app, "k8sresources")
        app.synth()
