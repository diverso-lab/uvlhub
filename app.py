from flask import jsonify
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import text
from flaskr import create_app, db

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

if __name__ == '__main__':
    app.run()
