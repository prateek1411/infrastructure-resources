from Stacks import CreateK8Stack
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return CreateK8Stack().create_stack()


if __name__ == '__main__':
    app.run()
