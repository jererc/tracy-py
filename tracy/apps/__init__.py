from flask import Flask

app = Flask(__name__)

from tracy.apps import api
