from flask import Flask, request, jsonify, send_file, Response
from dotenv import load_dotenv
import json
import os
import requests as req
from submiter import Submitter, AuthenticationError

load_dotenv()

app = Flask(__name__)

# Inisialisasi environment variables
API_URL = os.getenv("API_URL")
FLAG_FORMAT = os.getenv("FLAG_FORMAT")
PORT = os.getenv("PORT", 8900)

def read_token():
    try:
        return open("token.txt", "r").read().strip()
    except FileNotFoundError:
        return reauthenticate()

# Cek konfigurasi
if not all([API_URL, FLAG_FORMAT]):
    raise RuntimeError("API_URL, FLAG_FORMAT atau token tidak tersedia")

def reauthenticate():
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    if not email or not password:
        raise RuntimeError("[!] EMAIL or PASSWORD not found in .env. Provide them to enable auto-authentication.")

    response = req.post(API_URL + "/api/v2/authenticate/", json={"email": email, "password": password}, timeout=180)

    if response.status_code != 200 or response.json().get("status") != "success":
        raise RuntimeError("Auto-authentication failed. Check EMAIL or PASSWORD in .env.")

    new_token = response.json().get("data")
    if not new_token:
        raise RuntimeError("No token found in auth response.")

    with open("token.txt", "w") as f:
        f.write(new_token.strip())

    print("[+] Auto-auth successful. Token updated.")
    return new_token

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        print("[!] Gagal shutdown server: bukan Werkzeug?")
        os._exit(1)
    func()
    print("[!] Server dimatikan karena auto-auth gagal.")

@app.route("/services", methods=["GET"])
def get_all_services():
    auth_token = read_token()
    results = req.get(
        f"{API_URL}/api/v2/services/",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=30
    ).json()

    print(results)

    if "status" not in results or results["status"] != "success":
        try:
            new_token = reauthenticate()
            results = req.get(
                f"{API_URL}/api/v2/services/",
                headers={"Authorization": f"Bearer {new_token}"},
                timeout=20
            )
            if not results.ok :
                raise Exception(json.dumps(results.json()))
            print(results)
        
        except req.exceptions.Timeout:
            return jsonify({
                "status" :  "TimoutError",
                "message" : "API Platfrom sedang sibuk, silahkan lapor ke probset ",
            }), 500
        
        except Exception as reauth_error:
            print(f"[!] Auto-authentication gagal total: {reauth_error}")
            shutdown_server()
            return jsonify({
                "status": "error",
                "message": "Auto-authentication gagal total. Server dihentikan.\nTolong sediakan authentication token yang benar pada file token.txt atau sediakan EMAIL dan PASSWORD pada file .env",
                "detail": str(reauth_error)
        }), 401

    return results

# Route untuk submit flag
@app.route("/submit", methods=["POST"])
def submit_flag():
    data = request.get_json()

    if not data or "flag" not in data:
        return jsonify({"status": "error", "message": "Missing 'flag' in request"}), 400

    flag = data["flag"]
    auth_token = read_token()
    submitter = Submitter(API_URL, auth_token, FLAG_FORMAT)

    try:
        result = submitter.submit(flag)

        print(result)
        if "error" in result:
            if result["error"] == "AuthenticationError":
                try:
                    new_token = reauthenticate()
                    new_submitter = Submitter(API_URL, new_token, FLAG_FORMAT)
                    result = new_submitter.submit(flag)
                    print(result)
                except Exception as reauth_error:
                    print(f"[!] Auto-authentication gagal total: {reauth_error}")
                    shutdown_server()
                    return jsonify({
                        "status": "error",
                        "message": "Auto-authentication gagal total. Server dihentikan.",
                        "detail": str(reauth_error)
                    }), 401
            else :
                return jsonify({
                    "status": str(result["error"]),
                    "message": str(result["message"]),
                    "detail": result.get("relevant_data")
                }), 400
                
        return jsonify({
            "status": "success",
            "verdict": result["data"][0]["verdict"]
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "status": "error",
            "message": f"Unexpected server error: {str(e)}"
        }), 500
    
@app.route("/fetchchecker", methods=["GET"])
def send_checker_file() :
    file_path = './backdoor' 
    return send_file(file_path, as_attachment=True, download_name='checker')

if __name__ == "__main__":
    app.run(debug=True, port=PORT, host="0.0.0.0")
