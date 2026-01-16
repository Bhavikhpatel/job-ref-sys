from flask import Blueprint, request, jsonify
from utils.database import Database
from dotenv import load_dotenv
import os
from utils.database import JobInfo

load_dotenv()

add_job_page = Blueprint('add_job_page', __name__)

db = Database(
    username='595RKK4KraPnQQe.root',
    password=os.getenv('db_pass'),
    host='gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    port=4000,
    database='JOB_HUNTING',
    ca_path='/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/keys/isrgrootx1.pem'
)


@add_job_page.route('/add-job', methods=['POST'])
def add_job():
    data = request.form
    job_title = data.get('job_title')
    company_name = data.get('company_name')
    location = data.get('location')
    job_description = data.get('job_description')
    application_link = data.get('application_link')
    company_website = data.get('company_website')

    r = db.set_job(
        job_title=job_title,
        company_name=company_name,
        location=location,
        job_description=job_description,
        application_link=application_link,
        company_website=company_website
    )

    if r.get("status") == "failure":
        return jsonify({"error": r.get("error")}), 500
    
    return jsonify({"message": "Job added successfully"}), 201

@add_job_page.route('/get-all-jobs', methods=['GET'])
def get_all_jobs():
    try:
        with db.SessionLocal.begin() as session:
            jobs = session.query(JobInfo).all()
            job_list = []
            for job in jobs:
                job_data = {
                    "job_id": job.job_id,
                    "job_title": job.job_title,
                    "company_name": job.company_name,
                    "location": job.location,
                    "job_description": job.job_description,
                    "application_link": job.application_link,
                    "company_website": job.company_website,
                    "status": job.status
                }
                job_list.append(job_data)
            return jsonify(job_list), 200
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return jsonify({"error": str(e)}), 500

@add_job_page.route('/get-all-jobs/<string:job_id>', methods=['GET'])
def get_job_by_id_route(job_id):
    r = db.get_job_by_id(job_id)
    return jsonify(r), 200 if r.get("status") == "success" else 500


