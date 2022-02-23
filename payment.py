from import_reqs import *
from app import app

@app.route('/enterprise/stripe/attach', methods=['POST'])
def attach_payment_to_customer():
    """
        attach_payment_to_customer(): This is going to take in a company ID and attach a payment method to a customer object in Stripe
        Returns the customer's stripe ID
    """
    try:
        # Gets the data about the customer
        data = request.json["data"]
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            company_id = claims['uid']
            payment_method = data["payment_method"]

            # Retrieves the company's company ID & its stripe ID
            company_document_query = COMPANY.document(company_id)
            company_document = company_document_query.get().to_dict()
            customer_stripe_id = company_document["stripe_customer_id"]

            # Modifies the customer in Stripe
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_stripe_id,
            )
            stripe.Customer.modify(
                customer_stripe_id,
                invoice_settings={
                    'default_payment_method': payment_method
                }
            )
            # Returns success
            return jsonify({"success": True, 'customer_stripe_id': customer_stripe_id}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/enterprise/stripe/subscriptionstatus', methods=['POST'])
def is_customer_subscribed():
    """
        is_customer_subscribed(): Will take in a stripe customerID and check whether or not the customer is subscribed to the pricing plan or not as a boolean
    """
    try:
        # Gets the data about the customer
        data = request.json["data"]
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            customer_stripe_id = data["customer_stripe_id"]
            list_subscriptions = stripe.Subscription.list(
                customer=customer_stripe_id)
            subscriptions = list_subscriptions["data"]
            if len(subscriptions) == 0 or subscriptions[0]["status"] != "active":
                return jsonify({"success": True, 'is_subscribed': False}), 200
            else:
                return jsonify({"success": True, 'is_subscribed': True}), 200
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/stripe/payment', methods=['POST'])
def create_stripe_payment():
    """
        create_stripe_payment(): This is going to take in a customer ID and charge a specific price to their payment info. It is a one time transaction.
        Amount is in cents.
    """
    try:
        # Gets the data about the customer
        data = request.json["data"]
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            company_id = claims['uid']
            customer_stripe_id = data["customer_stripe_id"]
            amount = data["amount"]
            has_coupon = data["has_coupon"]

            # Retrieves the customer's default payment method to charge
            customer_object = stripe.Customer.retrieve(customer_stripe_id)
            default_payment_method = customer_object["invoice_settings"]["default_payment_method"]

            # Creates the PaymetIntent in Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=amount, currency="usd",
                customer=customer_stripe_id,
                confirm=True,
                payment_method=default_payment_method
            )

            # Retrieves the receipt for the transaction & stores it Firebase
            receipt_url = payment_intent["charges"]["data"][0]["receipt_url"]
            company_doc_query = COMPANY.document(company_id)
            company_doc = company_doc_query.get().to_dict()
            current_billing_history = company_doc['billing_history']
            current_billing_history.append(receipt_url)
            company_doc_query.update({
                'billing_history': current_billing_history
            })

            # Adds coupon after checking if one has been used
            if has_coupon == True:
                coupon_code = data["coupon_code"]
                coupon_doc_query = LOGS.document("coupons")
                coupon_doc = coupon_doc_query.get().to_dict()
                if coupon_code in coupon_doc.keys():
                    obj = {}
                    obj[coupon_code] = coupon_doc[coupon_code] + 1
                    coupon_doc_query.update(obj)
                else:
                    obj = {}
                    obj[coupon_code] = 1
                    coupon_doc_query.update(obj)
            # Returns success
            return jsonify({"success": True, 'receipt_url': receipt_url}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/stripe/customer', methods=['GET'])
def get_stripe_customer():
    """
        get_stripe_customer(): This is going to take in a Firebase ID and get the stripe customer object associated with that company
    """
    try:
        # Gets the data about the customer
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            company_id = claims['uid']
            company_doc = COMPANY.document(company_id).get().to_dict()

            stripe_customer_id = company_doc['stripe_customer_id']
            stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

            # Gets the payment method as well
            payment_method_id = stripe_customer["invoice_settings"]["default_payment_method"]
            payment_method = None
            if payment_method_id != None:
                payment_method = stripe.PaymentMethod.retrieve(
                    payment_method_id)

            return jsonify({"success": True, 'stripe_customer': stripe_customer, "payment_method": payment_method}), 200

    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/stripe/coupon', methods=['POST'])
def get_stripe_coupon():
    """
        get_stripe_coupon(): This is going to retrieve a Coupon based on its code
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            data = request.json["data"]
            coupon_code = data["coupon_code"]
            coupon = stripe.Coupon.retrieve(coupon_code)
            return jsonify({"success": True, 'coupon': coupon}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/stripe/subscribe', methods=['POST'])
def subscribe_customer():
    """
        subscribe_customer(): This is going to take in a stripe customer ID and subscribe a customer to our pricing
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        if claims['Enterprise'] is True:
            data = request.json["data"]
            stripe_customer_id = data["stripe_customer_id"]
            code_applied = data["code_applied"]
            if code_applied == "":
                stripe.Subscription.create(
                    customer=stripe_customer_id,
                    items=[
                        {"price": "price_1JFmYaCDrAwlb0oIYFYBMlIi"},
                    ],
                )
            else:
                stripe.Subscription.create(
                    coupon=code_applied,
                    customer=stripe_customer_id,
                    items=[
                        {"price": "price_1JFmYaCDrAwlb0oIYFYBMlIi"},
                    ],
                )
            return jsonify({"success": True, 'coupon': coupon}), 200
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An Error Occured: {e}"