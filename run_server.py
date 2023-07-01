from flask import Flask, render_template, request, jsonify
from load_google_sheet_data import GoogleSheet

app = Flask(__name__)

google_sheet = GoogleSheet()
@app.route("/")
def home():
    my_value = 10
    return render_template("index.html", value=my_value)

@app.route('/get_value')
def get_value():
    my_value = 10  # replace this with your own logic to get the value
    return jsonify({'value': my_value})

@app.route('/get_status_active')
def get_status_active():
    change_parts_json, clean_parts_json = google_sheet.get_item_by_stat_json(True)
    change_parts_expired_json, clean_parts_expired_json = google_sheet.get_item_by_stat_json(False)
    print(change_parts_json)
    return jsonify({'change_parts': change_parts_json, 
                    'clean_parts': clean_parts_json, 
                    'change_parts_expired': change_parts_expired_json, 
                    'clean_parts_expired': clean_parts_expired_json,})

@app.route('/load_google_sheet')
def load_google_sheet():
    google_sheet.load_house_appliance_df()
    change_parts_df, clean_parts_df = google_sheet.get_house_appliance_df()
    # print(change_parts_df)
    return jsonify({'result': 'ok'})

@app.route('/update_item', methods=['POST'])
def update_item():
    item_id = request.get_json()['item_id']
    print(item_id)
    if item_id is not None:
        google_sheet.update_item_status(item_id)
        print('Updated')
        response = {'status': 'success'}
    else:
        response = {'status': 'error', 'message': 'Item not found'}
    return jsonify(response)


if __name__ == "__main__":
    change_parts_df, clean_parts_df = google_sheet.get_house_appliance_df()
    print(change_parts_df)

    google_sheet.load_once_a_day()
    app.run(host='0.0.0.0', port=5001, 
            debug=True)
