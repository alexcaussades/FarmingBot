import json
import os
from time import sleep
import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import requests


load_dotenv()

FARMING_API_URL = os.getenv("FARMING_API_URL")
SERVEUR_FARMING_API_URL = os.getenv("SERVEUR_FARMING_API_URL")

class FarmingAPI:
    def __init__(self):
        self.farming_api_url = FARMING_API_URL
        self.serveur_farming_api_url = SERVEUR_FARMING_API_URL
        self.headers = {
            "Content-Type": "application/json"
        }


    def get_farming_data(self):
        try:
            response = requests.get(self.farming_api_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching farming data: {e}")
            return None
        
    def get_serveur_farming_parcels(self, id):
        try:
            response = requests.get(f"{self.farming_api_url}/{id}", headers=self.headers)
            response.raise_for_status()
            payload = response.json()
            # Retourner les informations du parcelle de farming pour l'ID '{id}'
            print(f"Fetching...'{id}'")
            sleep(1)
            status = payload.get('data', {}).get('status', 'N/A')
            active_reservation = payload.get('data', {}).get('active_reservation')
            reservation = "Aucune" if active_reservation is None else active_reservation
            Price = payload.get('data', {}).get('price')
            Price = Price.split(".")[0] if Price else "N/A"
            Price0 = str(Price)[:3]
            Price1 = str(Price)[3:] if Price else "N/A"
            Price = f"{Price0}.{Price1}" if Price0 and Price1 else "N/A"
            
            if status == 'reserved':
                player = active_reservation.get('player', {}) if isinstance(active_reservation, dict) else {}
                discord_id = player.get('discord_id') if isinstance(player, dict) else None
                discord_id = str(discord_id) if discord_id is not None else "N/A"
                print(f"Active reservation by Discord ID: {discord_id}")
                if discord_id != "N/A":
                    information = f"\n Hectares: {payload.get('data', {}).get('area', 'N/A')}\n Prix: {Price} €\n status : {status}\n ⚠️ Cette parcelle est actuellement réservée par <@{discord_id}>"
                else:
                    information = f"\n Hectares: {payload.get('data', {}).get('area', 'N/A')}\n Prix: {Price} €\n status : {status}\n ⚠️ Cette parcelle est actuellement réservée."
            else:
                information = f"\n Hectares: {payload.get('data', {}).get('area', 'N/A')}\n Prix: {Price} €\n status : {status}\n Tu peux réserver cette parcelle. alors dépêche-toi ! \n Pour réserver, utilise la commande /reserve {id}"
            return information
        except requests.RequestException as e:
            print(f"Error fetching serveur farming parcels: {e}")
            return None
        
    def push_reservation(self, id, reservation_data):
        print(f"Pushing reservation data for ID '{id}': {reservation_data}")
        discord_id = str(reservation_data.get('user_id'))
        print(f"Discord ID : {discord_id}")
        print(f"Farmland ID : {id}")
        
        discord_id = str(reservation_data.get('user_id'))
        
        payload = {"discord_id": discord_id}

        response = requests.post(
            f"{self.farming_api_url}/{id}/reserve",
            json=payload,
            headers=self.headers,
            timeout=15
        )
        return response.json() if response.status_code == 201 else None

    def cancel_reservation(self, id, reservation_data):
        print(f"Cancelling reservation for ID '{id}': {reservation_data}")
        discord_id = str(reservation_data.get('user_id'))
        print(f"Discord ID : {discord_id}")
        print(f"Farmland ID : {id}")

        payload = {"discord_id": discord_id}

        response = requests.delete(
            f"{self.farming_api_url}/{id}/reserve",
            json=payload,
            headers=self.headers,
            timeout=15
        )
        return response.json() if response.status_code == 200 else None
    
    def check_reservation(self, id):
        try:
            response = requests.get(f"{self.farming_api_url}/{id}/check", headers=self.headers)
            response.raise_for_status()
            payload = response.json()
            data = payload.get('data', {})
            status = data.get('status')
            if status is not None:
                return status
            reservation = payload.get('active_reservation')
            return reservation if reservation else "Aucune"
        except requests.RequestException as e:
            print(f"Error checking reservation for ID '{id}': {e}")
            return None
        
    def uptime(self):
        try:
            response = requests.get(f"{self.serveur_farming_api_url}/uptime", headers=self.headers)
            response.raise_for_status()
            payload = response.json()
            text = f"⏱️ Le serveur de farming {payload.get('Data', {}).get('Server', {}).get('name_serveur', 'N/A')} fonctionne depuis: {payload.get('Data', {}).get('Server', {}).get('uptime', 'N/A')} Actuellement il y a : {payload.get('Data', {}).get('Server', {}).get('players', 'N/A')} joueurs, Mods : {payload.get('Data', {}).get('Server', {}).get('Mods', 'N/A')}\n Statut du service Api: {payload.get('Data', {}).get('Api', {}).get('status', 'N/A')} en version {payload.get('Data', {}).get('Api', {}).get('version', 'N/A')}"
            return text
        except requests.RequestException as e:
            print(f"Error fetching uptime: {e}")
            return None