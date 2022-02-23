from import_reqs import *
from app import app

@app.route('/auth/enterprise', methods=['POST', 'GET'])
def create_company():
    """
        create_company(): companies can create a account.
    """
    now = datetime.now()
    try:

        # Fetches the data from the request object
        data = request.json['data']
        Company_name = 'C-'+data['company_name']
        Date = datetime.timestamp(now)
        Phone_number = data['phone_number']
        password = data['password']
        Email = data['email']
        Person_of_contact_first = data['first_name']
        Person_of_contact_last = data['last_name']
        Outreach_type = data['outreach_type']
        Company_logo = data['company_logo']
        survey_questions = data['survey_questions']
        user = auth.create_user(
            phone_number=Phone_number, password=password, email=Email, display_name=Company_name)
        auth.set_custom_user_claims(user.uid, {'Enterprise': True})
        # Creates the customer in stripe
        customer = stripe.Customer.create(
            email=Email,
            name=(Person_of_contact_first + " " + Person_of_contact_last),
            phone=Phone_number,
        )
        customer_stripe_id = customer.id

        # Adds the company to Firebase
        company_document = COMPANY.document(user.uid)
        company_document.set({
            'company_name': Company_name,
            'company_id': user.uid,
            'phone_number': Phone_number,
            'email': Email,
            'person_of_contact_first': Person_of_contact_first,
            'person_of_contact_last': Person_of_contact_last,
            'date': Date,
            'company_logo': Company_logo,
            'outreach_type': Outreach_type,
            'survey_questions': survey_questions,
            'stripe_customer_id': customer_stripe_id,
            'billing_history': [],
        })

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

