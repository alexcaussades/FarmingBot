import json
import os
from time import sleep
import discord
from discord import app_commands
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()
URL_TASKS = "http://127.0.0.1:8000/api/farmlands/tasks"

class TasksAPI:
    def __init__(self, url=URL_TASKS):
        self.url = url
    def get_tasks(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def get_task_by_id(self, task_id):
        response = requests.get(f"{self.url}/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def get_tasks_by_month(self, month):
        response = requests.get(f"{self.url}/month/{month}")
        if response.status_code == 200:
            data = response.json()
            # je cherche à ajouter des valeurs par défaut pour chaque tâche
            # {'data': [{'id': 4, 'player_id': '439378290344460301', 'farmland_id': 79, 'task_name': 'cleanners', 'month': 'décembre', 'created_at': None, 'updated_at': None, 'name': 'Alex', 'discord_id': '439378290344460301'}, {'id': 3, 'player_id': '1145762103655936122', 'farmland_id': 85, 'task_name': 'Action de nettoyage', 'month': 'décembre', 'created_at': None, 'updated_at': None, 'name': 'WiWi-GSP', 'discord_id': '1145762103655936122'}], 'count': 2}
            for i in range(len(data["data"])):
                data["data"][i]["task_name"] = data["data"][i].get("task_name", "")
                data["data"][i]["farmland_id"] = data["data"][i].get("farmland_id", "")
                data["data"][i]["name"] = data["data"][i].get("name", "")
            
            # toutes les tâches ont maintenant des valeurs par défaut pour les champs spécifiés
            # je veux retourner une chaîne de caractères contenant les informations de toutes les tâches
            info = ""
            for i in range(len(data["data"])):
                info += f"\n - Champs numéros  : **{data['data'][i]['farmland_id']}**,\n tâches à faire: **{data['data'][i]['task_name']}**,\n pour: **{data['data'][i]['name']}**\n"
            return info
        else:
            return None

    def create_task(self, month, task_data):
        
        task_data = {
            "player_id": str(task_data.get('player_id')),
            "farmland_id": task_data.get("farmland_id"),
            "task_name": task_data.get("task_name"),
            "month": task_data.get("month")
        }
        response = requests.post(f"{self.url}/create", json=task_data)
        if response.status_code == 201:
            return response.json()
        else:
            return None

    # Note: The player_id parameter is currently not used in the delete request.
    # If the API requires it, you may need to include it in the request body or headers.
    def delete_task(self, task_id, player_id=None):
        response = requests.delete(f"{self.url}/delete/{task_id}")
        if response.status_code == 204:
            return True
        else:
            return False