import os
import subprocess
import sys

import yaml
from decouple import config

from charts.application_charts import CreateChart
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
            values = json_data['values']
            values = os.path.join(os.path.dirname(os.path.realpath(__file__)), values)
            deployment_id = json_data['deployment_id']
            blueprint_id = json_data['blueprint_id']
            #auth_dict = json_data['auth_dict']
            CreateStack(deployment_id=deployment_id, blueprint_id=blueprint_id).create_stack(
                gen_code_dir=os.path.join(base_code_dir, 'terraform'), auth_dict=auth_dict, values=values)
            CreateChart(deployment_id=deployment_id, blueprint_id=blueprint_id).create_chart(
                gen_code_dir=os.path.join(base_code_dir, 'kubernetes'), values=values)

        except KeyError:
            print('Input Value not found')
            return jsonify("Unexpected error:", sys.exc_info()[0])
        return jsonify('Success')


@app.route('/infra-stack-list/<blueprint_id>/<deployment_id>', methods=['GET', 'POST'])
def infra_stack_list(blueprint_id, deployment_id):
    generated_files = {}
    if request.method == 'GET':
        blueprint_id = '' if id is None else blueprint_id
        for dirPath, subdirList, filelist in os.walk(os.path.join(base_code_dir, 'terraform',
                                                                  blueprint_id, deployment_id),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".terraform"]]
            tf_file_file = []
            for filename in filelist:
                tf_file_file.append(filename)
            if len(tf_file_file) != 0:
                generated_files[os.path.basename(dirPath)] = tf_file_file

    return jsonify(generated_files)


@app.route('/application-stack-list/<blueprint_id>/<deployment_id>', methods=['GET', 'POST'])
def application_stack_list(blueprint_id, deployment_id):
    generated_files = {}
    if request.method == 'GET':
        blueprint_id = '' if id is None else blueprint_id
        for dirPath, subdirList, filelist in os.walk(os.path.join(base_code_dir,
                                                                  'kubernetes', blueprint_id, deployment_id),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".terraform", ".dir"]]
            tf_file_file = []
            for filename in filelist:
                tf_file_file.append(filename)
            if len(tf_file_file) != 0:
                generated_files[os.path.basename(dirPath)] = tf_file_file

    return jsonify(generated_files)


@app.route('/application-viewcode/<blueprint_id>/<deployment_id>/<stack>/<code>', methods=['GET', 'POST'])
def view_tf_code(blueprint_id, deployment_id, stack, code):
    if request.method == 'GET':
        ret_code = {}
        filename = os.path.join(os.path.join(base_code_dir, 'kubernetes', blueprint_id, deployment_id, stack, code))
        with open(filename, mode='r') as file:
            data = yaml.load_all(file, Loader=yaml.FullLoader)
            for d in data:
                ret_code[d['kind']] = {}
                key = '{0}: {1}'.format(d['kind'], d['metadata']['name'])
                ret_code[d['kind']][d['metadata']['name']] = d
        print(ret_code)
        return jsonify(ret_code)


@app.route('/infra-code', methods=['POST'])
def apply_tf_code():
    if request.method == 'POST':
        json_data = request.get_json(force=True)

        try:
            deployment_id = json_data['deployment_id']
            blueprint_id = json_data['blueprint_id']
            stack = json_data['stack']
            command = json_data['command']
            tf_dir = os.path.join(base_code_dir, 'terraform', blueprint_id, deployment_id, stack)
            stack_command = 'terraform {0} -auto-approve {1}'.format(command, tf_dir)
            if command == 'init' or command == 'plan':
                stack_command = 'terraform {0} {1}'.format(command, tf_dir)
        except KeyError as key_error:
            print('Input Value not found')
            return jsonify("Unexpected error:", sys.exc_info()[0])
        cmd_output = __run_command(stack_command)
        return jsonify(cmd_output)


@app.route('/application-code', methods=['POST'])
def apply_app_code():
    if request.method == 'POST':
        json_data = request.get_json(force=True)

        try:
            deployment_id = json_data['deployment_id']
            blueprint_id = json_data['blueprint_id']
            stack = json_data['stack']
            command = json_data['command']
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
