from flask import Flask, render_template, request, make_response
import cohere
from dotenv import load_dotenv
import os
import pdfkit
import asyncio
from functools import lru_cache

load_dotenv()
app = Flask(__name__)
api_key = os.environ.get("COHERE_API_KEY")

current_question = {
    "question": "",
    "response": "",
    "outputanalysis": "",
    "reading": "",
    "practice": "",
    "review": ""
}


@lru_cache(maxsize=128)
def cached_runcohere(prompt_type, text):
    co = cohere.Client(api_key=api_key)
    prompt_map = {
        "response": text,
        "outputanalysis": f"Please generate detailed solutions for the following set of questions. For each question, provide a comprehensive solution{text}",
        "reading": f"Please explain the concept used to solve problem and briefly elaborate the concept. Recap all the formulae used and the terms used in those formulae{text}",
        "practice": f"Based on the given question, generate some more similar questions to the given question on similar concept. You can generate as many questions you want so that the concept is well practiced by the student using this to learn the concept{text}",
        "review": f"Based on the given question, generate some very short review and recap on the question and formulae and key concept included to solve the problem{text}"
    }
    response = co.generate(
        model='command-r-plus',
        prompt=prompt_map[prompt_type],
        max_tokens=4000
    )
    return response.generations[0].text


async def runcohere_async(prompt_type, text):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, cached_runcohere, prompt_type, text)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/ask', methods=['POST'])
def ask():
    global current_question
    question = request.form.get("question")
    if question == current_question.get("question"):
        response = current_question["response"]
        outputanalysis = current_question["outputanalysis"]
        reading = current_question["reading"]
        practice = current_question["practice"]
        review = current_question["review"]
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [
            runcohere_async("response", question),
            runcohere_async("outputanalysis", question),
            runcohere_async("reading", question),
            runcohere_async("practice", question),
            runcohere_async("review", question)
        ]
        response, outputanalysis, reading, practice, review = loop.run_until_complete(
            asyncio.gather(*tasks))
        current_question.update({
            "question": question,
            "response": response,
            "outputanalysis": outputanalysis,
            "reading": reading,
            "practice": practice,
            "review": review
        })

    return render_template("index.html", output=response, outputanalysis=outputanalysis, reading=reading, practice=practice, review=review)


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    question = current_question['question']
    response = current_question['response']
    outputanalysis = current_question['outputanalysis']
    practice = current_question['practice']
    review = current_question['review']
    reading = current_question.get('reading', '')

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
            .formula {{
                font-style: italic;
                white-space: pre-wrap; /* Ensures line breaks are respected */
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
                    <div class="answer-item">User's Question: {question}</div>
                    <div class="answer-item">Response: {response}</div>
                    <div class="answer-item">Output Analysis: <span class="formula">{outputanalysis}</span></div>
                </div>
            </div>
            <!-- Repeat the above structure for each question -->
        </div>

        <div class="section resource">
            <h2>Additional Resources</h2>
            <p>Reading material: {reading}</p>
            <p>Practice Questions: {practice}</p>
        </div>

        <div class="section">
            <h2>Conclusion</h2>
            <p>Recap key points and encourage further learning.</p>
        </div>

    </body>
    </html>
    '''

    options = {
        'quiet': '',
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'margin-right': '20mm'
    }

    try:
        pdf = pdfkit.from_string(html_content, False, options=options)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=document.pdf'
        return response
    except IOError as e:
        return f"An error occurred: {e}"


if __name__ == '__main__':
    app.run(debug=True)
