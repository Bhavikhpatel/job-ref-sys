from sqlalchemy import create_engine, URL, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.mysql import JSON
from dotenv import load_dotenv
import ulid

load_dotenv()

Base = declarative_base()

class JobInfo(Base):
    __tablename__ = 'Jobs'

    job_id = Column(String(100), primary_key=True)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    application_link = Column(String(500), nullable=False)
    status = Column(String(100), default="Pending")
    company_website = Column(String(500), nullable=False)

class PersonInfo(Base):
    __tablename__ = 'PersonInfo'

    job_id = Column(String(100), nullable=False)
    person_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    headline = Column(String(500), nullable=True)
    about = Column(Text, nullable=True)
    current_company = Column(String(255), nullable=True)
    current_job_title = Column(String(255), nullable=True)
    duration_in_current_company = Column(String(100), nullable=True)
    previous_experiences = Column(JSON, nullable=False)
    education = Column(JSON, nullable=False)
    additional_info = Column(JSON, nullable=True)
    status = Column(String(100), default="Not Connected")

class ChatHistory(Base):
    __tablename__ = 'ChatHistory'

    id = Column(String(100), primary_key=True, nullable=False)
    messages = Column(JSON, default=[])

class Database():
    def __init__(self, username, password, host, port, database, ca_path):
        
        self.url = URL.create(
            drivername="mysql+pymysql",
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        self.connect_args = {
            "ssl": {
                "ca": ca_path
            }
        }
        self.engine = create_engine(self.url, connect_args=self.connect_args)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def set_job(self, job_title, company_name, location, job_description, application_link, company_website):
        try:
            job_id=str(ulid.new())
            new_job = JobInfo(
                job_id=job_id,
                job_title=job_title,
                company_name=company_name,
                location=location,
                job_description=job_description,
                application_link=application_link,
                company_website=company_website
            )

            with self.SessionLocal.begin() as session:
                session.add(new_job)

            self.set_message(id=job_id, messages=[])
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to create job"
            }
        return {
            "status": "success"
        }

    def set_person(self, job_id, name, headline, about, current_company, current_job_title, duration_in_current_company, previous_experiences, education, additional_info):
        try:
            # Check if person with same name and company already exists
            with self.SessionLocal.begin() as session:
                existing_person = session.query(PersonInfo).filter(
                    PersonInfo.name == name,
                    PersonInfo.job_id == job_id
                ).first()
                if existing_person:
                    return {
                        "error": "Person with the same name and current company already exists for this job.",
                        "status": "failure"
                    }
            new_person = PersonInfo(
                person_id=str(ulid.new()),
                job_id=job_id,
                name=name,
                headline=headline,
                about=about,
                current_company=current_company,
                current_job_title=current_job_title,
                duration_in_current_company=duration_in_current_company,
                previous_experiences=previous_experiences,
                education=education,
                additional_info=additional_info
            )

            with self.SessionLocal.begin() as session:
                session.add(new_person)
                # Prepare the inserted person data to return
                person_data = {
                    "person_id": new_person.person_id,
                    "job_id": new_person.job_id,
                    "name": new_person.name,
                    "headline": new_person.headline,
                    "about": new_person.about,
                    "current_company": new_person.current_company,
                    "current_job_title": new_person.current_job_title,
                    "duration_in_current_company": new_person.duration_in_current_company,
                    "previous_experiences": new_person.previous_experiences,
                    "education": new_person.education,
                    "additional_info": new_person.additional_info,
                    "status": new_person.status,
                }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }
        return {
            "status": "success",
            "data": person_data
        }

    def update_person_status(self, person_id, status):
        try:
            with self.SessionLocal.begin() as session:
                person = session.query(PersonInfo).filter(PersonInfo.person_id == person_id).first()
                person.status = status
                session.add(person)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }
        return {
            "status": "success"
        }
        
    def get_person_by_id(self, person_id):
        try:
            with self.SessionLocal.begin() as session:
                person = session.query(PersonInfo).filter(PersonInfo.person_id == person_id).first()
                if not person:
                    return {
                        "error": "Person not found",
                        "status": "failure"
                    }
                person_data = {
                    "person_id": person.person_id,
                    "job_id": person.job_id,
                    "name": person.name,
                    "headline": person.headline,
                    "about": person.about,
                    "current_company": person.current_company,
                    "current_job_title": person.current_job_title,
                    "duration_in_current_company": person.duration_in_current_company,
                    "previous_experiences": person.previous_experiences,
                    "education": person.education,
                    "additional_info": person.additional_info,
                    "status": person.status
                }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }
        return {
            "data": person_data,
            "status": "success"
        }

    def get_job_by_id(self, job_id):
        try:
            with self.SessionLocal.begin() as session:
                job = session.query(JobInfo).filter(JobInfo.job_id == job_id).first()
                if not job:
                    return {
                        "error": "Job not found",
                        "status": "failure"
                    }
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
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }
        return {
            "data": job_data,
            "status": "success"
        }

    def set_message(self, id, messages):
        try:
            # first check if chat history exists for id
            with self.SessionLocal.begin() as session:
                chat = session.query(ChatHistory).filter(ChatHistory.id == id).first()
                if chat:
                    chat.messages = messages
                    session.add(chat)
                else:
                    new_chat = ChatHistory(
                        id=id,
                        messages=messages
                    )
                    session.add(new_chat)            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to set message"
            }
        return {
            "status": "success"
        }

    def get_message(self, id):
        try:
            with self.SessionLocal.begin() as session:
                chat = session.query(ChatHistory).filter(ChatHistory.id == id).first()
                if not chat:
                    return {
                        "error": "Chat history not found",
                        "status": "failure"
                    }
                messages = chat.messages
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to get chat history"
            }
        return {
            "data": messages,
            "status": "success"
        }

    def clear_messages(self, id):
        try:
            with self.SessionLocal.begin() as session:
                chat = session.query(ChatHistory).filter(ChatHistory.id == id).first()
                if chat:
                    chat.messages = []
                    session.add(chat)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to clear chat history"
            }
        return {
            "status": "success",
            "message": "Chat history cleared successfully"
        }
    
    def get_all_people(self, job_id):
        try:
            with self.SessionLocal.begin() as session:
                people = session.query(PersonInfo).filter(PersonInfo.job_id == job_id).all()
                people_list = []
                for person in people:
                    person_data = {
                        "person_id": person.person_id,
                        "job_id": person.job_id,
                        "name": person.name,
                        "headline": person.headline,
                        "about": person.about,
                        "current_company": person.current_company,
                        "current_job_title": person.current_job_title,
                        "duration_in_current_company": person.duration_in_current_company,
                        "previous_experiences": person.previous_experiences,
                        "education": person.education,
                        "additional_info": person.additional_info,
                        "status": person.status,
                    }
                    people_list.append(person_data)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to get people"
            }
        return {
            "data": people_list,    
            "status": "success",
            "message": "People retrieved successfully"
        }

    def get_all_connections(self, job_id):
        try:
            with self.SessionLocal.begin() as session:
                people = session.query(PersonInfo).filter(PersonInfo.job_id == job_id, PersonInfo.status != "Not Connected").all()
                people_list = []
                for person in people:
                    person_data = {
                        "person_id": person.person_id,
                        "job_id": person.job_id,
                        "name": person.name,
                        "headline": person.headline,
                        "about": person.about,
                        "current_company": person.current_company,
                        "current_job_title": person.current_job_title,
                        "duration_in_current_company": person.duration_in_current_company,
                        "previous_experiences": person.previous_experiences,
                        "education": person.education,
                        "additional_info": person.additional_info,
                        "status": person.status,
                    }
                    people_list.append(person_data)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to get connections"
            }
        return {
            "data": people_list,    
            "status": "success",
            "message": "Connections retrieved successfully"
        }


    def delete_person(self, person_id):
        try:
            with self.SessionLocal.begin() as session:
                person = session.query(PersonInfo).filter(PersonInfo.person_id == person_id).first()
                if not person:
                    return {
                        "error": "Person not found",
                        "status": "failure"
                    }
                session.delete(person)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to delete person"
            }
        return {
            "status": "success",
            "message": "Person deleted successfully"
        }

    def update_job_status(self, job_id, status):
        try:
            with self.SessionLocal.begin() as session:
                job = session.query(JobInfo).filter(JobInfo.job_id == job_id).first()
                job.status = status
                session.add(job)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }
        return {
            "status": "success"
        }
    
    def delete_job(self, job_id):
        try:
            with self.SessionLocal.begin() as session:
                job = session.query(JobInfo).filter(JobInfo.job_id == job_id).first()
                if not job:
                    return {
                        "error": "Job not found",
                        "status": "failure"
                    }
                session.delete(job)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to delete job"
            }
        return {
            "status": "success",
            "message": "Job deleted successfully"
        }

    def delete_person(self, person_id):
        try:
            with self.SessionLocal.begin() as session:
                person = session.query(PersonInfo).filter(PersonInfo.person_id == person_id).first()
                if not person:
                    return {
                        "error": "Person not found",
                        "status": "failure"
                    }
                session.delete(person)
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to delete person"
            }
        return {
            "status": "success",
            "message": "Person deleted successfully"
        }