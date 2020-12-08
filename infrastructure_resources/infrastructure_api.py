import os
import subprocess

from Stacks import CreateK8Stack
from flask import Flask, jsonify, request, make_response, json

app = Flask(__name__)


@app.route('/generate/', methods=['GET', 'POST'])
def create_stack():
    if request.method == 'GET':
        return jsonify(CreateK8Stack().create_stack())


@app.route('/stack-file-list/<file_path>/', methods=['GET', 'POST'])
def stack_file_list(file_path):
    generated_files = {}
    if request.method == 'GET':
        file_path = '' if id is None else file_path
        for dirPath, subdirList, filelist in os.walk(os.path.join(os.path.curdir, 'generated_code', file_path),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".terraform"]]
            tf_file_file = []
            for filename in filelist:
                tf_file_file.append(filename)
            if len(tf_file_file) != 0:
                generated_files[os.path.basename(dirPath)] = tf_file_file

    return jsonify(generated_files)


@app.route('/stacklist/', methods=['GET', 'POST'])
def stacklist():
    generated_files = {}
    if request.method == 'GET':
        for dirPath, subdirList, filelist in os.walk(os.path.join(os.path.curdir, 'generated_code'),
                                                     topdown=True):
            subdirList[:] = [d for d in subdirList if d not in [".terraform",".dir"]]
            tf_file_file = []
            for filename in filelist:
                tf_file_file.append(filename)
            if len(tf_file_file) != 0:
                generated_files[os.path.basename(dirPath)] = tf_file_file

    return jsonify(generated_files)


@app.route('/viewcode/<stack>/<code>', methods=['GET', 'POST'])
def view_tf_code(stack, code):
    if request.method == 'GET':
        filename = os.path.join(os.path.join(os.path.curdir, 'generated_code', stack, code))
        with open(filename) as file:
            data = json.load(file)
    return data


@app.route('/code/<stack>/<command>', methods=['GET', 'POST'])
def apply_tf_code(stack, command):
    if request.method == 'GET':
        tf_dir = os.path.join(os.path.curdir, 'generated_code', stack)
        tf_command = ['terraform', command, '-auto-approve', tf_dir]
        if command == 'init' or command == 'plan':
            tf_command = ['terraform', command, tf_dir]

        cmd_output = __run_command(tf_command)
        return jsonify(cmd_output)


def __run_command(tf_command):

    tf_apply = subprocess.Popen(tf_command, universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    output, error = tf_apply.communicate()
    cmd_output = {'output': output, 'error': error}
    return cmd_output


if __name__ == '__main__':
    #app.run()
    CreateK8Stack().create_stack()
