from flask import Flask, request 
from flask import render_template
import cohere
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
api_key = os.environ.get("COHERE_API_KEY")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    question = request.form.get("question")
    co = cohere.Client(api_key=api_key)
    response = co.chat(
       model="command-r-plus",
       message=question
       )
    return response.text

if __name__ == '__main__':
    app.run(debug=True)