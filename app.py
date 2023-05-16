from flask import jsonify, request
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import text
from flaskr import create_app, db
from zenodo import test_zenodo_connection,get_all_depositions

import os

load_dotenv(find_dotenv())
app = create_app()

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/env')
def show_env():
    env_vars = {key: value for key, value in os.environ.items()}
    return jsonify(env_vars)

@app.route('/test_db')
def test_db():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'message': 'Connection to the database successful'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/test_zenodo')
def test_zenodo():
    return jsonify(success=test_zenodo_connection())

@app.route('/test_get_all_depositions')
def test_get_all_depositions():
    return jsonify(get_all_depositions())

if __name__ == '__main__':
    app.run()
