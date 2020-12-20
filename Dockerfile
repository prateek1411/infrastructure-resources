FROM python:3.9-buster

RUN curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh

RUN bash nodesource_setup.sh
RUN apt-get install nodejs

ENV DEFAULT_TERRAFORM_VERSION=0.13.5                                \
    TF_PLUGIN_CACHE_DIR="/root/.terraform.d/plugin-cache"           \
    # MAVEN_OPTS is set in jsii/superchain with -Xmx512m. This isn't enough memory for provider generation.
    MAVEN_OPTS="-Xms256m -Xmx3G"

# Install Terraform
RUN AVAILABLE_TERRAFORM_VERSIONS="0.12.29 0.13.0 ${DEFAULT_TERRAFORM_VERSION}" && \
    for VERSION in ${AVAILABLE_TERRAFORM_VERSIONS}; do curl -LOk https://releases.hashicorp.com/terraform/${VERSION}/terraform_${VERSION}_linux_amd64.zip && \
    mkdir -p /usr/local/bin/tf/versions/${VERSION} && \
    unzip terraform_${VERSION}_linux_amd64.zip -d /usr/local/bin/tf/versions/${VERSION} && \
    ln -s /usr/local/bin/tf/versions/${VERSION}/terraform /usr/local/bin/terraform${VERSION};rm terraform_${VERSION}_linux_amd64.zip;done && \
    ln -s /usr/local/bin/tf/versions/${DEFAULT_TERRAFORM_VERSION}/terraform /usr/local/bin/terraform

#install cdktf
RUN npm install --global constructs@^3.0.0 eslint-plugin-react@7.21.5 eslint@^7 cdktf-cli@0.0.19 cdktf@0.0.19
#insall cdk8s
RUN npm install --global cdk8s-cli

#install kubectl
RUN curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
RUN chmod +x kubectl
RUN mv kubectl /usr/local/bin/


# Install infrastruture code

RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/
RUN mkdir -p /opt/app/pip_cache
COPY ./ /opt/app/
WORKDIR /opt/app/
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache
WORKDIR /opt/app/infrastructure_resources
RUN cdktf get
WORKDIR /opt/app/k8sresources
RUN cdk8s gen -l python
WORKDIR /opt/app/
STOPSIGNAL SIGTERM
EXPOSE 5000
CMD ["/bin/bash","/opt/app/infrastructure_resources/start-server.sh"]
