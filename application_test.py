#!/usr/bin/env python3
"""
Minimal test application for Elastic Beanstalk.
"""
from flask import Flask

application = Flask(__name__)

@application.route('/')
def index():
    return '<h1>Hello from Elastic Beanstalk!</h1><p>If you see this, the deployment is working.</p>'

@application.route('/health')
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=5000)

