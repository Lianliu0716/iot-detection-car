# -*- coding: utf-8 -*-
from flask import Flask,render_template
from tflite_runtime.interpreter import Interpreter
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('myDB.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def show():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM IOT').fetchall()
    conn.close()
    
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(port=8080, host ='0.0.0.0',debug=True)
