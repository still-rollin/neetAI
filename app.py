from flask import Flask, render_template, request, make_response
import cohere
from dotenv import load_dotenv
import os
import pdfkit

load_dotenv()

app = Flask(__name__)
api_key = os.environ.get("COHERE_API_KEY")

current_question = {
    "question": "",
    "response": ""
}

def runcohere(text):
    co = cohere.Client(api_key=api_key)
    response = co.generate(
        model='command-r-plus',
        prompt=text,
        max_tokens=50
    )
    print(response.generations[0].text)
    return response.generations[0].text

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    global current_question
    print("Asking question")
    current_question.clear()
    question = request.form.get("question")
    response = runcohere(question)
    current_question['question'] = question
    current_question['response'] = response
    return render_template("index.html", output=response)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    question = current_question['question']
    response = current_question['response']
    
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>neetAI Analysis Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
            }}
            .cover {{
                text-align: center;
                margin-bottom: 50px;
            }}
            .cover img {{
                width: 200px; /* Adjust size as needed */
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
            }}
            .subtitle {{
                font-size: 18px;
                color: #666;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .question {{
                margin-bottom: 20px;
            }}
            .question-text {{
                font-weight: bold;
            }}
            .answers {{
                margin-left: 20px;
            }}
            .answer-item {{
                margin-bottom: 10px;
            }}
            .resource {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="cover">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgeJZ1-kpxgyXxYga7doCUZbWH5tS7JAt2zA&s" alt="neetAI Logo">
            <div class="title">Analysis Report</div>
            <div class="subtitle">Questions and Answers Analysis</div>
        </div>

        <div class="section">
            <h2>Summary</h2>
            <p>Total marks obtained: [Insert dynamic data here]</p>
        </div>

        <div class="section">
            <h2>Detailed Analysis</h2>
            <div class="question">
                <div class="question-text">Question 1:</div>
                <div class="answers">
                    <div class="answer-item">User's Answer: {question}</div>
                    <div class="answer-item">Correct Answer: {response}</div>
                    <div class="answer-item">Explanation: {response}</div>
                </div>
            </div>
            <!-- Repeat the above structure for each question -->
        </div>

        <div class="section resource">
            <h2>Additional Resources</h2>
            <p>Reading material: [Insert links or descriptions here]</p>
            <p>Practice Questions: {response}</p>
        </div>

        <div class="section">
            <h2>Conclusion</h2>
            <p>Recap key points and encourage further learning.</p>
        </div>

    </body>
    </html>
    '''

    # Specify the path to your fonts directory if necessary
    options = {
        'quiet': ''
    }

    try:
        # Generate PDF from HTML content
        pdf = pdfkit.from_string(html_content, False, options=options)
        
        # Prepare and return the PDF as response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=document.pdf'
        return response
    except IOError as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)
