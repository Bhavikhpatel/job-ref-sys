from flask import Blueprint, request, jsonify
from utils.large_language_model import LLM
from utils.database import Database
from dotenv import load_dotenv
import os

load_dotenv()

dashboard_page = Blueprint('dashboard_page', __name__)

db = Database(
    username='595RKK4KraPnQQe.root',
    password=os.getenv('db_pass'),
    host='gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    port=4000,
    database='JOB_HUNTING',
    ca_path='/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/keys/isrgrootx1.pem'
)

llm = LLM()

@dashboard_page.route('/add-person', methods=['POST'])
def add_person():
    data = request.form

    job_id = data.get('job_id')
    profile_text = data.get('profile_text')

    r = llm.get_profile_json(profile_text=profile_text)

    if r.get("status") == "failure":
        return jsonify({"error": r.get("error")}), 500

    r = db.set_person(
        job_id=job_id,
        name=r["data"].get("name"),
        headline=r["data"].get("headline"),
        about=r["data"].get("about"),
        current_company=r["data"].get("current_company"),
        current_job_title=r["data"].get("current_job_title"),
        duration_in_current_company=r["data"].get("duration_in_current_company"),
        previous_experiences=r["data"].get("previous_experiences"),
        education=r["data"].get("education"),
        additional_info=r["data"].get("additional_info")
    )

    if r.get("status") == "failure":
        return jsonify({"error": r.get("error")}), 500  
    
    # Return the newly created person object
    return jsonify(r), 201

@dashboard_page.route('/add-connection/<string:person_id>', methods=['PUT'])
def add_connection(person_id):
    r = db.update_person_status(person_id, "Connected")
    
    if r.get("status") == "failure":
        return jsonify({"error": r.get("error")}), 500
    
    return jsonify(r), 200


@dashboard_page.route('/generate-cold-message/<string:person_id>', methods=['GET'])
def generate_message(person_id):
    r = llm.generate_cold_message(db, person_id)
    
    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/send-follow-up/<string:person_id>', methods=['POST'])
def send_follow_up(person_id):
    data = request.form
    new_message = data.get('message')

    if not new_message or new_message.strip() == "":
        return jsonify({"error": "Message cannot be empty"}), 400

    # Fetch existing chat
    person_chat = db.get_message(id=person_id)

    if person_chat.get("status") == "failure":
        return jsonify(person_chat), 500

    if person_chat["data"] == []:
        return jsonify({
            "error": "No existing conversation found. Please start a new chat first."
        }), 400
    messages = person_chat["data"]

    # Append user message (Gemini format)
    messages.append({
        "role": "user",
        "parts": [{"text": new_message.strip()}]
    })
###############
    # Send updated conversation to Gemini
    r = llm.get_follow_up_response(db=db,
        prompt=messages,
        person_id=person_id
    )

    if r.get("status") == "failure":
        return jsonify(r), 500

    return jsonify(r), 200 

@dashboard_page.route('/chat-history/<string:person_id>', methods=['GET'])
def chat_history(person_id):
    r = db.get_message(id=person_id)
    
    # If no chat history exists, return empty messages instead of error
    if r.get("status") == "failure":
        return jsonify({
            "data": [],
            "status": "success"
        }), 200
    
    return jsonify(r), 200

@dashboard_page.route('/clear-history/<string:person_id>', methods=['DELETE'])
def clear_history(person_id):
    r = db.clear_messages(person_id)

    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/get-all-people/<string:job_id>', methods=['GET'])
def get_all_people(job_id):
    r = db.get_all_people(job_id)

    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/get-all-connections/<string:job_id>', methods=['GET'])
def get_all_connections(job_id):
    r = db.get_all_connections(job_id)

    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/delete-person/<string:person_id>', methods=['DELETE'])
def delete_person(person_id):
    r = db.delete_person(person_id)

    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/update-person-status/<string:person_id>', methods=['PUT'])
def update_person_status(person_id):
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    r = db.update_person_status(person_id, status)
    
    return jsonify(r), 200 if r.get("status") == "success" else 500


@dashboard_page.route('/update-job-status/<string:job_id>', methods=['PUT'])
def update_job_status(job_id):
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    r = db.update_job_status(job_id, status)

    return jsonify(r), 200 if r.get("status") == "success" else 500

@dashboard_page.route('/delete-job/<string:job_id>', methods=['DELETE'])
def delete_job(job_id):
    r = db.delete_job(job_id)

    return jsonify(r), 200 if r.get("status") == "success" else 500
