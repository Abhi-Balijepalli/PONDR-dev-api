from import_reqs import *
from app import app

@app.route('/enterprise/products', methods=['GET'])
def get_products_by_company():
    """
         get_products_by_company(id): this will be for company dashboard.
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            query_ref = PRODUCT.where(u'Company_id', u'==', uid)
            documents = [doc.to_dict() for doc in query_ref.stream()]
            return (jsonify({"company_products": documents}), 200)
        else:
            return (jsonify("You are not authorized to view this page"), 403)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/product=<id>/pin', methods=['POST'])
def pin_product(id):
    """
        pin_product(id): This is going to update the pinned flag in the product collection
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            pinned = data['pinned']
            PRODUCT.document(id).update({"pinned": pinned})
            return (jsonify({"success": True, }), 200)
        else:
            return (jsonify("You are not authorized to view this specific enterprise analytics page."), 403)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/createProduct', methods=['POST'])
def create_product():
    """
         create_product(): a product entry for a enterprise (NOT ACTIVATED FOR REVIEW GURUS ANALYTICS).
    """
    now = datetime.now()
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            Category = data['Category']
            Company_name = data['Company_name']
            Company_id = uid
            Date = datetime.timestamp(now)
            Product_id = str(Date) + uid
            Product_name = data['Product_name']
            Competitor_flag = data['Competitor_flag']
            Amazon_link = data['amazon_link']
            product_document = PRODUCT.document(Product_id)
            product_document.set({
                'Category': Category,
                'Company_name': Company_name,
                'Company_id': Company_id,
                'Product_entry_date': Date,
                'Product_id': Product_id,
                # this is the path on google firestore Storage for images
                'Product_images_path': "enterprise/"+str(Product_id)+"/",
                'Product_name': Product_name,
                'Amazon_link': Amazon_link,
                'processed': False,
                'assigned': False,
                'competitor_product': Competitor_flag,
                'review_guru_analytics': False,
                'projects': []
            })
            return jsonify({"success": True}), 200
        else:
            return (jsonify("You are not authorized to view this page"), 404)
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/project/add', methods=['POST']) # You can add multiple existing products to a project
def add_product_to_project():
    """
        add_product_to_project(): add single/multiple products to a project
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            project_name = data['project_name']
            products = data['products'] #this should be an array of productIDs
            product_document = PRODUCT.document(Product_id)
            product_document_json = product_document.get().to_dict()
            if product_document_json['projects'] is None:
                product_document.set({
                    "projects":[]
                },merge=True)
                product_document_json = product_document.get().to_dict() # i am refetching becuase i want to reinitialize the dict, with the "projects": []
            for i in products:                
                if len(product_document_json['projects']) < 3:
                    new_arr = product_document_json['projects']
                    new_arr.append(project_name)
                    product_document.set({
                        "projects":new_arr
                    }, merge=True)
                else:
                   jsonify({"Error": "You can add a single product to a max of 3 projects"}), 404 
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/enterprise/reanalyzeProduct', methods=['POST'])
def reanalyze_product():
    """
        reanalyze_product(): This is going to mark a product for reanalysis
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            data = request.json['data']
            product_id = data['product_id']
            PRODUCT.document(product_id).update({
                'reanalyze': True
            })

            return jsonify({"success": True}), 200
        else:
            return (jsonify("You are not authorized to view this page"), 404)
    except Exception as e:
        return f"An Error Occured: {e}"
