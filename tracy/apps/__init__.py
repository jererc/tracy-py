import logging

from flask import Flask

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

from tracy.apps import api
