from systools.system import webapp

from tracy.apps import app

from tracy import settings


def run():
    webapp.run(app, host='0.0.0.0', port=settings.API_PORT)
