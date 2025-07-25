from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# config database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Flask!"})

if __name__ == '__main__':
    app.run(debug=True)
