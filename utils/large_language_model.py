from google import genai
from dotenv import load_dotenv
import os
from string import Template
import json

# Load environment variables
load_dotenv()

api_key = os.getenv("gemini_api_key")
if not api_key:
    raise EnvironmentError("gemini_api_key not found in environment variables")


class LLM:
    def __init__(self):
        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)

    def get_profile_json(self, profile_text: str) -> dict:
        try:
            # Load prompt template
            with open(
                "/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/prompts/profile_extractor.txt",
                "r",
                encoding="utf-8"
            ) as f:
                prompt_template = Template(f.read())

            prompt = prompt_template.substitute(profile_text=profile_text)

            # Generate content (JSON enforced)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )

            # Parse JSON output
            output = json.loads(response.text)

        except FileNotFoundError:
            return {
                "error": "Prompt file not found",
                "status": "failure"
            }

        except json.JSONDecodeError:
            return {
                "error": "Model did not return valid JSON",
                "status": "failure"
            }

        except (AttributeError, TypeError):
            return {
                "error": "Empty or invalid response from model",
                "status": "failure"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failure"
            }

        return {
            "data": output,
            "status": "success"
        }

    def generate_cold_message(self, db, person_id):
        try:
            person_data = db.get_person_by_id(person_id)

            if person_data.get("status") == "failure":
                return {
                    "error": person_data.get("error"),
                    "status": "failure"
                }

            employee_information = f"name: {person_data['data']['name']}\n" \
                                f"headline: {person_data['data']['headline']}\n" \
                                f"about: {person_data['data']['about']}\n" \
                                f"current_company: {person_data['data']['current_company']}\n" \
                                f"current_job_title: {person_data['data']['current_job_title']}\n" \
                                f"duration_in_current_company: {person_data['data']['duration_in_current_company']}\n" \
                                f"previous_experiences: {person_data['data']['previous_experiences']}\n" \
                                f"education: {person_data['data']['education']}\n" \
                                f"additional_info: {person_data['data']['additional_info']}\n"

            job_data = db.get_job_by_id(person_data["data"]["job_id"])

            if job_data.get("status") == "failure":
                return {
                    "error": job_data.get("error"),
                    "status": "failure"
                }

            job_description = f"job_title: {job_data['data']['job_title']}\n" \
                            f"company_name: {job_data['data']['company_name']}\n" \
                            f"job_description: {job_data['data']['job_description']}\n" \
                            f"application_link: {job_data['data']['application_link']}\n"

            with open("/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/prompts/company_information.txt", 'r', encoding='utf-8') as f:
                prompt_template = Template(f.read())

            prompt = prompt_template.substitute(company_website=job_data["data"]["company_website"])

            response = self.client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )

            company_info = response.text.strip()
        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to retrieve necessary data"
            }

        try:
            with open("/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/prompts/cold_message.txt", 'r', encoding='utf-8') as f:
                message_template = Template(f.read())
            
            message_prompt = message_template.substitute(
                employee_information=employee_information,
                job_description=job_description,
                company_information=company_info
            )

            response = self.client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=message_prompt,
            )

            cold_message = response.text.strip()
            conversation = [
                            {
                                "role": "user",
                                "parts": [{"text": message_prompt}]
                            },
                            {
                                "role": "model",
                                "parts": [{"text": cold_message}]
                            }
                        ]

            db.set_message(id=person_id, messages=conversation)

        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to generate cold message"
            }

        return {
            "status": "success",
            "message": "Cold message generated successfully"
        }

    def get_follow_up_response(self, db, prompt: list, person_id: str) -> dict:
        try:
            # prompt is ALREADY in Gemini format:
            # [{ "role": "...", "parts": ["..."] }, ...]

            response = self.client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt
            )

            chat_response = response.text.strip()

            # Append model reply in Gemini format
            prompt.append({
                "role": "model",
                "parts": [{"text": chat_response}]
            })

            # Store updated conversation
            db.set_message(id=person_id, messages=prompt)

        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to get follow-up response"
            }

        return {
            "status": "success",
            "message": "Follow-up response generated successfully"
        }

    def dictionary_from_llm_gemini(self, db, job_id, current_resume_score, current_docx_text, job_description, remarks) -> dict:

        prompt_template_path = "/home/bhavikhpatel/job_referral_software_ver_1.0/ver_1.1/prompts/resume_prompt.txt"
        try:
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                prompt_template = Template(f.read())

            prompt = prompt_template.substitute(
                current_resume_score=current_resume_score,
                current_resume_text=current_docx_text,
                job_description=job_description,
                remarks = remarks
            )
            # fetch the row from table ChatHistory job_id = job_id, if not present create one
            r = db.get_message(job_id)
            if r.get("status") == "failure":
                return {
                    "error": r.get("error"),
                    "status": "failure"
                }
            messages = r["data"]

            if len(messages) == 0:
                json_prompt = [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            else:
                json_prompt = messages
                json_prompt.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                )
            
            
            response = self.client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=json_prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            
            db.set_message(person_id=job_id, messages=json_prompt + [{
                "role": "model",
                "parts": [{"text": response.text.strip()}]
            }])
            
            output = json.loads(response.text)

        except FileNotFoundError:
            return {
                "error": "Prompt file not found",
                "status": "failure"
            }

        except json.JSONDecodeError:
            return {
                "error": "Model did not return valid JSON",
                "status": "failure"
            }

        except (AttributeError, TypeError):
            return {
                "error": "Empty or invalid response from model",
                "status": "failure"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failure",
                "message": "Failed to get profile json"
            }

        return output










