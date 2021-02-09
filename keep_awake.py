from threading import Thread
from flask import Flask
application = Flask('')
@application.route('/')
def home():
    return "I am awake... yaaawn"
def run():
  application.run(host='0.0.0.0',port=8080)
def keep_awake():
    d = Thread(target=run)
    d.start()