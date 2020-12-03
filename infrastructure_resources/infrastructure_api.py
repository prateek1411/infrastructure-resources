import os

from Stacks import CreateK8Stack
from flask import Flask
from flask_autoindex import AutoIndex
app = Flask(__name__)
AutoIndex(app, browse_root=os.path.join(os.path.curdir,'generated_code'))

@app.route('/generate')
def hello_world():
    return CreateK8Stack().create_stack()

if __name__ == '__main__':
    app.run()
