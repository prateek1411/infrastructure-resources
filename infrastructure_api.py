import os
import subprocess
import sys

import yaml
from decouple import config

from k8sresources.charts.application_charts import CreateChart
from infrastructure_resources.create_stack import CreateStack
from flask import Flask, jsonify, request, json

app = Flask(__name__)
auth_dict = {"subscription_id": config('subscription_id'), "client_id": config('client_id'),
             "client_secret": config('client_secret'), "tenant_id": config('tenant_id'),
             "access_key": config('access_key')}
base_code_dir = os.path.dirname(os.path.realpath(__file__))
values = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'values.yaml')


@app.route('/generate/', methods=['POST'])
def create_stack():
    if request.method == 'POST':
        json_data = request.get_json(force=True)

        try:
            deployment_variables = json_data['deployment_variables']
            #            deployment_variables = os.path.join(os.path.dirname(os.path.realpath(__file__)), deployment_variables)
            deployment_id = json_data['deployment']
            blueprint_id = json_data['blueprint']
            # auth_dict = json_data['auth_dict']
            CreateStack(deployment_id=deployment_id, blueprint_id=blueprint_id).create_stack(
                gen_code_dir=os.path.join(base_code_dir, 'terraform'), auth_dict=auth_dict,
                deployment_variables=deployment_variables)
            CreateChart(deployment_id=deployment_id, blueprint_id=blueprint_id).create_chart(
                gen_code_dir=os.path.join(base_code_dir, 'kubernetes'), values=deployment_variables)
        except KeyError:
            print('Input Value not found')
            return jsonify(stack_created=False)
        return jsonify(stack_created=True)


@app.route('/infra-stack-list/<blueprint_id>/<deployment_id>', methods=['GET', 'POST'])
def infra_stack_list(blueprint_id, deployment_id):
    generated_files = {}
    if request.method == 'GET':
        blueprint_id = '' if id is None else blueprint_id
        for dirPath, subdirList, filelist in os.walk(os.path.join(base_code_dir, 'terraform',
                                                                  blueprint_id, deployment_id),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".terraform"]]
            tf_file_file = {}
            for filename in filelist:
                with open(os.path.join(dirPath, filename), mode='r') as file:
                    data = json.load(file)
                    tf_file_file[filename] = data
            if len(tf_file_file) != 0:
                generated_files[os.path.basename(dirPath)] = tf_file_file

    return jsonify(deployment=deployment_id, code=generated_files)


@app.route('/application-stack-list/<blueprint_id>/<deployment_id>', methods=['GET', 'POST'])
def application_stack_list(blueprint_id, deployment_id):
    generated_files = {}
    if request.method == 'GET':
        blueprint_id = '' if id is None else blueprint_id
        for dirPath, subdirList, filelist in os.walk(os.path.join(base_code_dir,
                                                                  'kubernetes', blueprint_id, deployment_id,
                                                                  'kubectl_manifest'),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".kubeconfig", ".dir"]]
            ret_code = {}
            for filename in filelist:
                with open(os.path.join(dirPath, filename), mode='r') as file:
                    data = yaml.load_all(file, Loader=yaml.FullLoader)
                    for d in data:
                        ret_code[d['kind']] = {}
                        key = '{0}: {1}'.format(d['kind'], d['metadata']['name'])
                        ret_code[d['kind']][d['metadata']['name']] = d
            if len(ret_code) != 0:
                generated_files[os.path.basename(dirPath)] = ret_code
    return jsonify(deployment=deployment_id, code=generated_files)


@app.route('/infra-code', methods=['POST'])
def apply_tf_code():
    if request.method == 'POST':
        json_data = request.get_json(force=True)
        try:
            deployment_id = json_data['deployment']
            blueprint_id = json_data['blueprint']
            stack = json_data['stack_name']
            tf_dir = os.path.join(base_code_dir, 'terraform', blueprint_id, deployment_id, stack)
            stack_command = 'terraform init {0}'.format(tf_dir)
            __run_command(stack_command)
            stack_command = 'terraform apply -auto-approve {0}'.format(tf_dir)
            cmd_output = __run_command(stack_command)
            return jsonify(cmd_output)
        except KeyError as key_error:
            print('Input Value not found')
            return jsonify("Unexpected error:", sys.exc_info()[0])


@app.route('/application-code', methods=['POST'])
def apply_app_code():
    if request.method == 'POST':
        json_data = request.get_json(force=True)

        try:
            deployment_id = json_data['deployment']
            blueprint_id = json_data['blueprint']
            stack = json_data['stack_name']
            command = 'apply'
            kubeconconfig = os.path.join(base_code_dir, 'terraform', blueprint_id, deployment_id, 'generated_files')
            kube_manifest = os.path.join(base_code_dir, 'kubernetes', blueprint_id, deployment_id, stack)
            stack_command = 'kubectl {0} --kubeconfig {1} -f {2}'.format(command, kubeconconfig, kube_manifest)
        except KeyError as key_error:
            print('Input Value not found')
            return jsonify("Unexpected error:", sys.exc_info()[0])

        cmd_output = __run_command(stack_command)
        return jsonify(cmd_output)


def __run_command(command):
    tf_apply = subprocess.Popen(args=command, universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    output, error = tf_apply.communicate()
    cmd_output = {'output': output, 'error': error}
    return cmd_output


if __name__ == '__main__':
    app.run()
    # CreateK8Stack(gen_code_dir).create_stack(auth_dict=auth_dict,values=values)
    # application_charts.create_chart(gen_code_dir,values)
