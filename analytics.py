from import_reqs import *
from app import app

@app.route('/enterprise/product=<id>', methods=['GET'])
def get_advanced_analytics(id):
    """
         get_advanced_analytics(id): this will be for company dashboard, they will see the advanced analytics of a product.
    """
    try:
        id_token = request.headers['Authorization']
        claims = auth.verify_id_token(id_token)
        uid = claims['uid']
        if claims['Enterprise'] is True:
            todo = ADVANCED_ANALYTICS.document(id).get().to_dict()
            if todo['company_id'] == uid:
                return jsonify(todo), 200
            else:
                return (jsonify({"Access Denied"}), 403)
        else:
            return (jsonify("You are not authorized to view this specific enterprise analytics page."), 403)
    except Exception as e:
        return f"An Error Occured: {e}"