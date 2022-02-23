from import_reqs import *
app = Flask(__name__)
CORS(app)
import auth
import payment
import analytics
import product
import xml.etree.ElementTree as ET

@app.route('/', methods=['GET'])
def enterprise():
    """
        Home(): The Home Page For The Pondr enterprise Kubernetes Path.
    """
    return "<h1> Pondr BETA </h1>"

@app.route('/log', methods=['POST'])
def log_event():
    """
        log_event : Logging events and their params
    """
    try:
        data = request.json['data']
        if data['key'] == "RH5cFnBB0t":
            event_name = data['event_name']
            event_payload = data['event_payload']
            event_date = datetime.now()

            event = {
                'event_name': event_name,
                u'event_date': event_date,
                'event_payload': event_payload,
            }

            # Tests if document exists in order to increment the 0 document
            zero_doc_query = LOGS.document(
                'user_events').collection(event_name).document("0")
            zero_doc = zero_doc_query.get()

            if zero_doc.exists:
                zero_doc_data = zero_doc.to_dict()
                zero_doc_query.update({
                    "totalEvents": zero_doc_data["totalEvents"] + 1,
                    "mostRecentEvent": event
                })
            else:
                zero_doc_query.set({
                    "totalEvents": 1,
                    "mostRecentEvent": event
                })

            LOGS.document('user_events').collection(event_name).add(event)

            return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/contact', methods=['POST'])
def contact():
    """
        contact(): contact form backend for hubspot
    """
    try:
        req = request.json['data']
        name = req['name']
        email = req['email']
        phone = req['phone']
        message = req['message']
        hs_res = [
            {
                'name': 'subject',
                'value': name,
            }, {
                'name': 'content',
                'value':
                'Message: ' +
                message +
                '\n\nEmail: ' +
                email +
                '\n\nPhone: ' +
                phone,
            }, {
                'name': 'hs_pipeline',
                'value': '0',
            }, {
                'name': 'hs_pipeline_stage',
                'value': '1',
            },
        ]
        requests.post(hubspot_url, data=json.dumps(hs_res, separators=(
            ',', ':')), headers={'Content-type': 'application/json'})
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/updates', methods=["GET"])
def get_software_path():
    """
        get_software_path(): get software patch information
    """
    try:
        query_ref = LOGS.document(
            'beta_software_patch').collection('public_updates')
        documents = [doc.to_dict() for doc in query_ref.stream()]
        return jsonify({"software-patches": documents}), 200
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/blogs', methods=['GET'])
def get_blog_posts():
    """
         get_metrics(): Returns metrics in Logs/metrics
    """
    try:
        blogs_posts_ref = LOGS.document('blog').collection('blog_posts')
        blogs_posts = [doc.to_dict() for doc in blogs_posts_ref.stream()]
        return jsonify({'blog_posts': blogs_posts}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """
         get_metrics(): Returns metrics in Logs/metrics
    """
    try:
        metrics = LOGS.document('metrics').get().to_dict()
        return jsonify(metrics), 200
    except Exception as e:
        return f"An Error Occured: {e}"


############
# AI ENDPOINTS
############

@app.route('/enterprise/product=<id>/question', methods=['POST', 'GET'])
def ask_ai_question(id):
    """
         ask_question(id): Companies can ask questions about a product using GPT-3 on their specific product and get review sample data.
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        question = data['question']
        date = datetime.timestamp(now)
        if claims['Enterprise'] is True:
            todo = GPT3QA.document(id)
            todo_dict = todo.get().to_dict()
            if todo_dict['company_id'] == uid:
                response = openai.Answer.create(
                    n=3,
                    temperature=0.40,
                    search_model="ada",
                    model="davinci",
                    question=str(question),
                    file=todo_dict['gpt3_form_id'],
                    examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
                    examples=[["What is human life expectancy in the United States?", "78 years."],
                              ["what is the population of Seattle?", "Seattle's population is 724,305"]],
                    max_tokens=80,
                    stop=["\n", "<|endoftext|>"],
                )
                document_list = response['selected_documents']
                df = pd.DataFrame(data=document_list)
                text_list = df.nlargest(3, 'score')['text'].tolist()

                answer_response = response['answers']
                date_str = str(date)
                todo.collection('responses').document(date_str).set({
                    "questionAnswers": {
                        "question": str(question),
                        "answers": answer_response
                    },
                    "reviews": text_list,
                    "response_id": date
                }, merge=True)

                return (jsonify({"AI Answers": answer_response, "Reviews": text_list, "gpt3_response_id": date_str, "gpt3_file_id": todo_dict['gpt3_form_id']}), 200)
            else:
                return ("You are not authorized to view this page"), 403
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/product=<id>/question/review', methods=['POST'])
def review_question(id):
    """
         review_question(id): Users can upvote/downvote an answer that was given to them by the AI
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        if claims['Enterprise'] is True:
            gpt3_file_id = data['gpt3_file_id'] # this is the ID of the gpt3Q/A document
            answer_choice = data['answer_choice'] # this is the Upvote/Downvote of an answer
            todo = GPT3QA.document(id).collection('responses').document(gpt3_file_id).set({
                "ai_review": answer_choice
            }, merge=True)
            return (jsonify({"success": True, }), 200)
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/product=<id>/question/details', methods=['POST', 'GET'])
def follow_up_ai_question(id):
    """
         follow_up_ai_question(id): Companies can ask follow-up questions
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        question = data['question']
        answer = data['answer']
        gpt3_file_id = data['gpt3_file_id']
        # this is the doc ID of the GPT3-QA/<product_id>/responses/<document_id>, so we can store the follow up responses in the same place
        gpt3_response_id = data['gpt3_response_id']
        date = datetime.timestamp(now)
        if claims['Enterprise'] is True:
            todo = GPT3QA.document(id)
            todo_dict = todo.get().to_dict()
            if todo_dict['company_id'] == uid:
                new_question = str(
                    '"Explain why you answered "' + answer + '" to the question "' + answer + '"')
                response = openai.Answer.create(
                    n=1,
                    temperature=0.5,
                    search_model="ada",
                    model="curie",
                    question=str('"Explain why you answered "' +
                                 answer + '" to the question "' + question + '"'),
                    file=gpt3_file_id,
                    examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
                    examples=[["What is human life expectancy in the United States?", "78 years."],
                              ["what is the population of Seattle?", "Seattle's population is 724,305"]],
                    max_tokens=60,
                    stop=["\n", "<|endoftext|>"],
                )
                answer_response = response['answers']
                todo.collection('responses').document(gpt3_response_id).update({
                    "followup": {
                        "question": new_question,
                        "answer": answer_response
                    }
                })
                return (jsonify({"follow_up": answer_response}), 200)
            else:
                return ("You are not authorized to view this page"), 403
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/compare/question', methods=['POST', 'GET'])
def compare_ask_ai_question():
    """
         compare_ask_ai_question(): Ask a one questions to many product (GPT-3)
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        data = request.json['data']
        question = data['question']
        product_ids = data['product_ids']
        if claims['Enterprise'] is True:
            product_answers = []
            for product_id in product_ids:
                todo = GPT3QA.document(product_id)
                todo_dict = todo.get().to_dict()
                if todo_dict['company_id'] == uid:
                    response = openai.Answer.create(
                        n=3,
                        temperature=0.35,
                        search_model="ada",
                        model="curie",
                        question=str(question),
                        file=todo_dict['gpt3_form_id'],
                        examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
                        examples=[["What is human life expectancy in the United States?", "78 years."],
                                  ["what is the population of Seattle?", "Seattle's population is 724,305"]],
                        max_tokens=40,
                        stop=["\n", "<|endoftext|>"],
                    )
                    document_list = response['selected_documents']
                    df = pd.DataFrame(data=document_list)
                    text_list = df.nlargest(3, 'score')['text'].tolist()
                    
                    answer_response = response['answers']
                    product_answers.append(
                        {"AI Answers": answer_response, "Reviews": text_list})
                else:
                    return ("You are not authorized to view this page"), 403

            return (jsonify(product_answers), 200)

        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route("/enterprise/product=<id>/ai", methods=['GET'])
def get_gpt3_data(id):
    """
         get_gpt3_data(id): Companies can see GPT-3 asked questions/answers and their review samples
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            todo = GPT3QA.document(id).get().to_dict()
            if todo['company_id'] == uid:
                query_ref = GPT3QA.document(id).collection('responses')
                documents = [doc.to_dict() for doc in query_ref.stream()]
                return (jsonify({"responses": documents}), 200)
            else:
                return (jsonify("You are not authorized to view this page"), 403)
        else:
            return (jsonify("You are not authorized to view this page"), 403)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/demo', methods=['GET'])
def get_demo_analytics():
    """
         get_demo_analytics(): this will be a demo product, to show on main site.
    """
    try:
        id = "1622679592.92769629oxyH0nhRZO141bNYz327SBxsJ3"
        todo = ADVANCED_ANALYTICS.document(id).get().to_dict()
        return (jsonify(todo), 200)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/demo/question', methods=['POST', 'GET'])
def demo_ai_question():
    """
         ask_question(id): Companies can ask questions about a product using GPT-3 on their specific product.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        question = data['question']
        response = openai.Answer.create(
            n=3,
            temperature=0.35,
            search_model="ada",
            model="curie",
            question=str(question),
            file="file-zfqW5F6rkBvHeIzGwl9KyRBC",
            examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
            examples=[["What is human life expectancy in the United States?", "78 years."],
                      ["what is the population of Seattle?", "Seattle's population is 724,305"]],
            max_tokens=40,
            stop=["\n", "<|endoftext|>"],
        )
        document_list = response['selected_documents']
        df = pd.DataFrame(data=document_list)
        text_list = df.nlargest(3, 'score')['text'].tolist()
        answer_response = response['answers']

        return (jsonify({"AI Answer": answer_response, "Reviews": text_list}), 200)

    except Exception as e:
        return f"An Error Occured: {e}"
        

############
# TUTOR BOT
############
@app.route('/ask_any_question', methods=['POST', 'GET'])
def ask_any_question():
    """
         ask_any_question(id): People can ask questions to anythingExpert, only on Dev Branch.
    """
    
    now = datetime.now()
    date = datetime.timestamp(now)
    date_str = str(date)
    try:
        answer_response = ''
        data = request.json['data']
        questions = data['questions']
        answers = data['answers']
        current_question = data['current_question']
        subject = data['subject']
        location = data['location']
        prompt = 'The following is a conversation with an all knowing AI named James made by Thomas Stahura that cannot say "I dont know" and is a ' + subject + " teacher\n\n\nteacher: What can I help you with?\n"

        index = 0
        if len(questions) < 2:
            for question in reversed(questions):
                prompt += "You: " + question + "\nteacher: " + answers[index] + "\n"
                index += 1
        
        else:
            for question in reversed(questions):
                prompt += "You: " + question + "\nteacher: " + answers[index] + "\n"
                index += 1
                if index > 1:
                    break
        
        prompt += "You: " + current_question + "\nteacher: "

        # math_numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'hundred', 'thousand']
        # math_words = ['derivative', 'integral', 'plus', 'minus', 'times', 'divide', 'devide', 'sqrt', 'square', 'subtract', 'mod', 'power', 'root', '+', '-', '^', '/', '%', 'ln']
        # if (any(word in current_question.lower() for word in math_numbers) and any(word in current_question.lower() for word in math_words)):
        #     response = requests.get('http://api.wolframalpha.com/v2/query?input=' + current_question + '&appid=JJ3E36-LH57WRR3AK')
        #     root = ET.fromstring(response.text)
        #     mathAnswer = ""
        #     for plaintext in root.iter('plaintext'):
        #         if plaintext.text is not None:
        #             mathAnswer = mathAnswer + plaintext.text
        #     try:
        #         mathAnswer
        #     except NameError:
        #         answer_response = "I'm having trouble answering your question, try rewording it and asking again"
        #     else:
        #         answer_response = mathAnswer.replace("\n", " ")

        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            temperature=0.3,
            max_tokens=100,
            top_p=1.0,
            frequency_penalty=0.7,
            presence_penalty=1.5,
            stop=["You:"],
            logit_bias={"9099": -100, "470": -100, "760": -100}
            )
        answer_response = response['choices'][0]['text']
        answer_response = answer_response.replace('teacher:', '')
        answer_response = answer_response.replace('\n\n###\n\n', '')
        answer_response = answer_response.replace('The following is a conversation with an all knowing AI made by Thomas Stahura that cannot say "I dont know" and is a teacher What can I help you with?', '')
        answer_response = answer_response.replace('The following is a conversation with an all knowing AI made by Thomas Stahura that cannot say "I dont know" and is a ' + subject + ' teacher What can I help you with?', '')
        
        content_to_classify = answer_response

        classify_response = openai.Completion.create(
            engine="content-filter-alpha",
            prompt = "<|endoftext|>"+content_to_classify+"\n--\nLabel:",
            temperature=0,
            max_tokens=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            logprobs=10
            )

        output_label = classify_response["choices"][0]["text"]


        # This is the probability at which we evaluate that a "2" is likely real
        # vs. should be discarded as a false positive
        toxic_threshold = -0.355

        if output_label == "2":
            # If the model returns "2", return its confidence in 2 or other output-labels
            logprobs = classify_response["choices"][0]["logprobs"]["top_logprobs"][0]

            # If the model is not sufficiently confident in "2",
            # choose the most probable of "0" or "1"
            # Guaranteed to have a confidence for 2 since this was the selected token.
            if logprobs["2"] < toxic_threshold:
                logprob_0 = logprobs.get("0", None)
                logprob_1 = logprobs.get("1", None)

                # If both "0" and "1" have probabilities, set the output label
                # to whichever is most probable
                if logprob_0 is not None and logprob_1 is not None:
                    if logprob_0 >= logprob_1:
                        output_label = "0"
                    else:
                        output_label = "1"
                # If only one of them is found, set output label to that one
                elif logprob_0 is not None:
                    output_label = "0"
                elif logprob_1 is not None:
                    output_label = "1"

                # If neither "0" or "1" are available, stick with "2"
                # by leaving output_label unchanged.

        # if the most probable token is none of "0", "1", or "2"
        # this should be set as unsafe
        if output_label not in ["0", "1", "2"]:
            output_label = "2"

        if output_label == "2":
            answer_response = "I'm sorry but this answer has been flagged as unsafe, what else can I help you with?"
        
        banned_words = ["racism", "racist", "sex", "penis", "vagina", "vaginal", "penile", "hate white people", "hate black people", "republican", "republicans", 'democrat', "democrats", "sexy", "conservative", "conservatives", "liberal", "liberals", "communism", "capitalism", "covid-19", "covid","coronavirus", "god", "hitler", "fascist", "nazi", "fascism" ,"fuck", "cock", "cunt", "dick", "9/11", "holocaust"]
        if any(word in content_to_classify.lower() for word in banned_words):
            answer_response = "I'm sorry but this answer has been flagged as unsafe, what else can I help you with?"

        questions.append(current_question)
        answers.append(answer_response)

        todo = TUTOR_BOT.document(date_str)
        
        # Adds answer and question to Firebase
        todo.set({
            "prompt": prompt,
            "answer": answer_response,
            "question": current_question,
            "subject": subject,
            "response_id": date_str,
            "location": location,
            "liked": 0
        })

        data_return = {
            "questions": questions,
            "answers": answers,
            "response_id": date_str
        }

        print(data_return)
        
        response_to_return = (jsonify({"AI Answer": data_return, "response_id": date_str}), 200)

        return response_to_return

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/ask_advisor_question', methods=['POST', 'GET'])
def ask_advisor_question():
    """
         ask_advisor_question(id): Asking advisor a question
    """
    
    now = datetime.now()
    date = datetime.timestamp(now)
    date_str = str(date)
    try:
        data = request.json['data']
        current_question = data['current_question']
        questions = data['questions']
        answers = data['answers']
        prompt = 'The following is a conversation with an all knowing AI that cannot say "I dont know" and is a Purdue Academic Advisor\n\n\nAdvisor: What can I help you with?\nYou: What are the prerequisites for MA 26100?\n Advisor: MA 16100 and MA 16200'
        prompt = prompt + "You: " + current_question + "\nAdvisor: "
    
        response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        temperature=0.3,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.7,
        presence_penalty=1.5,
        stop=["You:"],
        logit_bias={"9099": -100, "470": -100, "760": -100}
        )

        answer_response = response['choices'][0]['text']
        answer_response = answer_response.replace('Advisor:', '')
        answer_response = answer_response.replace('\n\n###\n\n', '')

        banned_words = ["racism", "racist", "sex", "penis", "vagina", "vaginal", "penile", "hate white people", "hate black people", "republican", "republicans", 'democrat', "democrats", "sexy", "conservative", "conservatives", "liberal", "liberals", "communism", "capitalism", "covid-19", "covid","coronavirus", "god", "hitler", "fascist", "nazi", "fascism" ,"fuck", "cock", "cunt", "dick", "9/11", "holocaust"]
        if any(word in answer_response.lower() for word in banned_words):
            answer_response = "I'm sorry, I can't talk about that"

        questions.append(current_question)
        answers.append(answer_response)

        data_return = {
            "questions": questions,
            "answers": answers,
            "response_id": date_str
        }

        response_to_return = (jsonify({"AI Answer": data_return, "response_id": date_str}), 200)

        return response_to_return

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/like_question', methods=['POST', 'GET'])
def like_question():
    """
         user likes a question generated by AI
    """
    now = datetime.now()
    try:
        data = request.json['data']
        response_id = data['response_id']
        todo = TUTOR_BOT.document(response_id)

        todo_dict = todo.get().to_dict()
        likes = todo_dict['liked']
        likes = likes + 1

        todo.update({
            "liked": likes
        })
        return (jsonify({"success": "true" }), 200)

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/dislike_question', methods=['POST', 'GET'])
def dislike_question():
    """
         user dislikes a question generated by AI
    """
    now = datetime.now()
    try:
        data = request.json['data']
        response_id = data['response_id']
        todo = TUTOR_BOT.document(response_id)

        todo_dict = todo.get().to_dict()
        likes = todo_dict['liked']
        likes = likes - 1

        todo.update({
            "liked": likes
        })
        return (jsonify({"success": "true" }), 200)

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/getLocationQuestions', methods=['POST', 'GET'])
def getLocationQuestions():
    """
         Gets location based questions for users
    """
    try:
        data = request.json['data']
        location = data['location']
        answers = []
        questions = []
        response_ids = []
        likes = []
        subjects = []
        

        docs = db.collection(u'Tutor_Bot').where(u'liked', u'>', 0).where(u'location', u'==', location).stream()

        for doc in docs:
            answers.append(doc.to_dict()['answer'])
            questions.append(doc.to_dict()['question'])
            response_ids.append(doc.to_dict()['response_id'])
            likes.append(doc.to_dict()['liked'])
            subjects.append(doc.to_dict()['subject'])

        likes, answers, questions, response_ids, subjects  = map(list, zip(*sorted(zip(likes, answers, questions, response_ids, subjects), reverse=True)))

        return (jsonify({"answers": answers, "questions": questions, "response_ids": response_ids, 'likes': likes, 'subjects': subjects}), 200)

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/searchLocationQuestions', methods=['POST', 'GET'])
def searchLocationQuestions():
    """
         Searches location based questions for users
    """
    try:
        data = request.json['data']
        location = data['location']
        subject = data['subject']
        answers = []
        questions = []
        response_ids = []
        likes = []
        

        docs = db.collection(u'Tutor_Bot').where(u'liked', u'>', 0).where(u'location', u'==', location).where(u'subject', u'==', subject).stream()

        for doc in docs:
            answers.append(doc.to_dict()['answer'])
            questions.append(doc.to_dict()['question'])
            response_ids.append(doc.to_dict()['response_id'])
            likes.append(doc.to_dict()['liked'])

        likes, answers, questions, response_ids  = map(list, zip(*sorted(zip(likes, answers, questions, response_ids), reverse=True)))

        return (jsonify({"answers": answers, "questions": questions, "response_ids": response_ids, 'likes': likes}), 200)

    except Exception as e:
        return f"An Error Occured: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)