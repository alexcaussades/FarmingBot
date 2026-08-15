from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==========================================================
# CONFIGURATION
# ==========================================================

HOST = "0.0.0.0"
PORT = 8080

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_TEST")
API_KEY = os.environ.get("Pc_windows")


# ==========================================================
# DISCORD
# ==========================================================

def send_discord(message):
    data = {
        "content": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(DISCORD_WEBHOOK, json=data, headers=headers)
    if response.status_code != 204:
        print(f"Failed to send message to Discord: {response.status_code} - {response.text}")