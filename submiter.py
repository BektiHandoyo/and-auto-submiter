import requests as req
from dotenv import load_dotenv
import os
import sys

load_dotenv()

class InvalidRequestError(Exception):
    def __init__(self, message, relevant_data):
        super().__init__(message)
        self.message = message 
        self.relevant_data = relevant_data

    def __str__(self):
        return f"{self.message}\n{self.relevant_data}"

class AuthenticationError(Exception):
    pass

class Submitter :
    def __init__(self, platform_url, auth_token, flag_format) :
        self.platform_url = platform_url
        self.auth_token = auth_token
        self.flag_format = flag_format

    def submit(self, flag):
        try :
            if self.flag_format not in flag :
                raise InvalidRequestError(f"[-] Invalid Flag, please check the submitted flag or check the currently used flag format with the competition flag format", {"flag_format" : self.flag_format, "submitted_flag" : flag})
        
            submit_flag = req.post(
                url=self.platform_url+"/api/v2/submit",
                headers={ "Authorization" : f"Bearer {self.auth_token}"},
                json={ "flags" : [flag] },
                timeout=180
            )

            if submit_flag.status_code == 403 :
                raise AuthenticationError("[-] Autehentication Failed, please check the authentication token")
            
            submit_flag_response = submit_flag.json()


            if submit_flag_response["data"][0]["verdict"] == "flag is wrong or expired." :
                raise InvalidRequestError("[-] Submited flag is wrong or expired.", {"Flag" : flag})
            
            if not submit_flag.ok :
                raise InvalidRequestError(f"[-] Something Went Wrong", submit_flag_response)

            if submit_flag_response["data"][0]["verdict"] in ["flag is correct.", "flag already submitted."] :
                print("[+] Flag is successfully submitted!")
                return submit_flag_response
                
        except InvalidRequestError as invalid_req_error: 
            return {"error" : "InvalidRequestError", "message" : invalid_req_error.message, "relevant_data" : invalid_req_error.relevant_data}
        
        except AuthenticationError as auth_error :
            return {"eror" : "AuthenticationError","message" : auth_error}
        
        except req.exceptions.Timeout:
            return {"error": "TimeoutError", "message": "[-] Request to platform timed out after 3 seconds", "flag" : flag}

if __name__ == "__main__" :
    try :
        flag = sys.argv[1]

        api_url = os.getenv("API_URL")
        flag_format = os.getenv("FLAG_FORMAT")
        auth_token = open("token.txt", "r").read().strip()

        if not auth_token :
            raise FileNotFoundError()

        if not api_url or not flag_format:
            raise Exception("Please add API_URL and FLAG_FORMAT variable on your .env file")

        submitter = Submitter(api_url, auth_token, flag_format)
        submit_res = submitter.submit(flag)
        print(submit_res)
    except IndexError:
        print("Please Provide the flag that want to be submitted \ne.g python3 submitter.py flag{fake_flag}")

    except Exception as error:
        print(error)

