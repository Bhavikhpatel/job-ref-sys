from flask import Flask
from add_job_page import add_job_page
from dashboard_page import dashboard_page
from flask_cors import CORS


app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

app.register_blueprint(add_job_page)
app.register_blueprint(dashboard_page)
