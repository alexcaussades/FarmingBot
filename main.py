from ast import Not
import discord
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import requests
import json
from module.recolte.recolte import get_recolte_info, list_crops, add_crop
from module.mounth.up_mouth import connect_db, close_connection, update_mouth_task, get_mouth_tasks
import sqlite3
import logging
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()
Serveur_info_live = os.getenv('Serveur_Stats')
Serveur_carriere_live = os.getenv('Serveur_Career')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True
webhook_url = os.environ.get("DISCORD_WEBHOOK")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_TEST")
API_KEY = os.environ.get("Pc_windows")
app = Flask(__name__)

HOST = "0.0.0.0"
PORT = 8080

# ==========================================================
# Elite Dangerous Events
# ==========================================================

app = Flask(__name__)

@app.route('/FarmingBot', methods=['POST'])
def handle_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée JSON reçue"}), 400

    event_type = data.get("event")
    if not event_type:
        return jsonify({"error": "Aucun type d'événement spécifié"}), 400

    # Log the received event
    logging.info(f"Événement reçu: {event_type} - Données: {data}")

    # Handle specific events
    if event_type == "FarmingBot":
        # Process the FarmingBot event
        logging.info("Traitement de l'événement FarmingBot")
        # Add your processing logic here

    return jsonify({"status": "success", "message": f"Événement {event_type} traité avec succès"}), 200



# ===========================================================
# DISCORD EVENTS
# ===========================================================



@client.event
async def on_ready():
   print(f"Bot connecté en tant que {client.user}")
   await client.change_presence(activity=discord.Game(name=os.getenv('MessageServeur') + "V" + os.getenv('Version')))
   requests.post(webhook_url, json={"content": f"🤖 Le bot s'est connecté en tant que {client.user}"})



@client.event
async def on_member_join(member):
    # Attribuer automatiquement le rôle "Membres" au nouveau membre
    role = discord.utils.get(member.guild.roles, name="Membres")
    if role is not None:
        try:
            await member.add_roles(role)
            print(f"Rôle 'Membres' attribué à {member.name}")
        except discord.Forbidden:
            print(f"❌ Je n'ai pas la permission d'ajouter le rôle à {member.name}")
        except Exception as e:
            print(f"❌ Erreur lors de l'attribution du rôle: {str(e)}")
    else:
        print(f"⚠️ Le rôle 'membre' n'existe pas sur le serveur")

@client.event
async def on_message_delete(message):
    # Événement déclenché quand un message est supprimé
    if message.author == client.user:
        return
    requests.post(webhook_url, json={"content": f"🗑️ Message supprimé de {message.author.name}: {message.content[:100]}"})

@client.event
async def on_message_edit(before, after):
    # Événement déclenché quand un message est modifié
    if before.author == client.user:
        return
    if before.content != after.content:
        requests.post(webhook_url, json={"content": f"✏️ {before.author.name} a modifié un message:\nAvant: {before.content[:100]}\nAprès: {after.content[:100]}"})

@client.event
async def on_member_remove(member):
    # Événement déclenché quand un membre quitte le serveur
    requests.post(webhook_url, json={"content": f"👋 {member.name} a quitté le serveur"})

@client.event
async def on_message(message):
    member = message.author.id
    
    if message.author == client.user:
        return

    if message.content.startswith('!bonjour'):
        staff_role = discord.utils.get(message.guild.roles, name="STAFF")
        if staff_role in message.author.roles:
            await message.channel.send(f"Bonjour {message.author.name}, Voici l'un de mes maîtres")
        else:
            await message.channel.send("Bonjour " + message.author.name + " ! 👋")

    if message.content.startswith('!help'):
        await message.channel.send("\n **Commandes disponibles :**\n"
                                   "• `!bonjour` : Le bot vous salue.\n"
                                   "• `!purge <nombre>` : Supprime un nombre spécifié de messages (Rôle requis: STAFF ou VIP).\n"
                                   "• `!kick <@utilisateur> [raison]` : Expulse un utilisateur du serveur (Rôle requis: STAFF ou VIP).\n"
                                   "• `!addrole <@utilisateur> <@rôle>` : Ajoute un rôle à un utilisateur (Rôle requis: STAFF).\n"
                                   "• `!rmrole <@utilisateur> <@rôle>` : Retire un rôle d'un utilisateur (Rôle requis: STAFF).\n"
                                   "• `!getrole <nom_du_rôle>` : Demande un rôle au STAFF.\n"
                                   "• `!recolte <type_de_culture>` : Obtient les informations de semis et récolte pour une culture spécifique.\n"
                                    )

    if message.content.startswith('!purge'):
        # Vérifier si l'utilisateur a le rôle "staff" ou "VIP"
        staff_role = discord.utils.get(message.guild.roles, name="STAFF")
        vip_role = discord.utils.get(message.guild.roles, name="VIP")
        if staff_role not in message.author.roles and vip_role not in message.author.roles:
            await message.channel.send("❌ Vous n'avez pas les permissions pour utiliser cette commande. Rôles requis: STAFF ou VIP")
            return
        
        try:
            # Extraire le nombre de messages à supprimer
            args = message.content.split()
            if len(args) < 2:
                await message.channel.send("❌ Usage: !purge <nombre>")
                return
            
            amount = int(args[1])
            if amount <= 0 or amount > 100:
                await message.channel.send("❌ Le nombre doit être entre 1 et 100")
                #envoyer un webhook au channel de log
                requests.post(webhook_url, json={"content": f"⚠️ {message.author.name} a tenté d'utiliser la commande purge avec un nombre invalide: {amount}"})
                return
            
            # Supprimer les messages (amount + 1 pour inclure la commande)
            deleted = await message.channel.purge(limit=amount + 1)
            await message.channel.send(f"✅ {len(deleted) - 1} message(s) supprimé(s)", delete_after=5)
            requests.post(webhook_url, json={"content": f"✅ {message.author.name} a supprimé {len(deleted) - 1} message(s) dans le channel {message.channel.name}"})
            
        except ValueError:
            await message.channel.send("❌ Veuillez entrer un nombre valide")
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de supprimer les messages")
            requests.post(webhook_url, json={"content": f"❌ {message.author.name} a tenté d'utiliser la commande purge mais le bot n'a pas les permissions nécessaires."})

    if message.content.startswith('!kick'):
        # Vérifier si l'utilisateur a le rôle "STAFF" ou "VIP"
        staff_role = discord.utils.get(message.guild.roles, name="STAFF")
        vip_role = discord.utils.get(message.guild.roles, name="VIP")
        if staff_role not in message.author.roles and vip_role not in message.author.roles:
            await message.channel.send("❌ Vous n'avez pas les permissions pour utiliser cette commande. Rôles requis: STAFF ou VIP")
            return
        
        try:
            # Extraire le membre à kick
            args = message.content.split()
            if len(args) < 2:
                await message.channel.send("❌ Usage: !kick <@utilisateur> [raison]")
                return
            
            # Récupérer le membre mentionné
            if not message.mentions:
                await message.channel.send("❌ Veuillez mentionner un utilisateur")
                return
            
            member = message.mentions[0]
            reason = " ".join(args[2:]) if len(args) > 2 else "Aucune raison fournie"
            
            # Vérifier que le bot peut kick ce membre
            if member.top_role >= message.author.top_role:
                await message.channel.send("❌ Vous ne pouvez pas kick un membre de rang égal ou supérieur")
                requests.post(webhook_url, json={"content": f"⚠️ {message.author.name} a tenté d'utiliser la commande kick sur un membre de rang égal ou supérieur: {member.name}"})
                return
            
            # Kick le membre
            await member.kick(reason=reason)
            await message.channel.send(f"✅ {member.name} a été kick du serveur. Raison: {reason}")
            requests.post(webhook_url, json={"content": f"✅ {message.author.name} a kické {member.name} du serveur. Raison: {reason}"})
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de kick ce membre")
            requests.post(webhook_url, json={"content": f"❌ {message.author.name} a tenté d'utiliser la commande kick mais le bot n'a pas les permissions nécessaires."})
        except Exception as e:
            await message.channel.send(f"❌ Une erreur s'est produite: {str(e)}")

    if message.content.startswith('!addrole'):
        # Vérifier si l'utilisateur a le rôle "Bureau"
        staff_role = discord.utils.get(message.guild.roles, name="STAFF")
        if staff_role not in message.author.roles:
            await message.channel.send("❌ Vous n'avez pas les permissions pour utiliser cette commande. Rôle requis: STAFF")
            return
        
        try:
            # Extraire le membre et le rôle à ajouter
            args = message.content.split()
            if len(args) < 3:
                await message.channel.send("❌ Usage: !addrole <@utilisateur> <@rôle>")
                return
            
            # Récupérer le membre mentionné
            if not message.mentions:
                await message.channel.send("❌ Veuillez mentionner un utilisateur")
                return
            
            member = message.mentions[0]
            # Extraire l'ID du rôle mentionné
            role_id = int(args[2].strip('<@&>'))
            role = message.guild.get_role(role_id)
            
            if role is None:
                await message.channel.send(f"❌ Le rôle avec l'ID {role_id} n'existe pas")
                return
            
            # Ajouter le rôle au membre
            await member.add_roles(role)
            await message.channel.send(f"✅ Le rôle '@{role.name}' a été ajouté à {member.name}")
            requests.post(webhook_url, json={"content": f"✅ {message.author.name} a ajouté le rôle '@{role.name}' à {member.name}"})
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission d'ajouter ce rôle")
            requests.post(webhook_url, json={"content": f"❌ {message.author.name} a tenté d'utiliser la commande addrole mais le bot n'a pas les permissions nécessaires."})
        except Exception as e:
            await message.channel.send(f"❌ Une erreur s'est produite: {str(e)}")
            
    if message.content.startswith('!rmrole'):
        # Vérifier si l'utilisateur a le rôle "Bureau"
        staff_role = discord.utils.get(message.guild.roles, name="STAFF")
        if staff_role not in message.author.roles:
            await message.channel.send("❌ Vous n'avez pas les permissions pour utiliser cette commande. Rôle requis: STAFF")
            return
        
        try:
            # Extraire le membre et le rôle à retirer
            args = message.content.split()
            if len(args) < 3:
                await message.channel.send("❌ Usage: !removerole <@utilisateur> <nom_du_rôle>")
                return
            
            # Récupérer le membre mentionné
            if not message.mentions:
                await message.channel.send("❌ Veuillez mentionner un utilisateur")
                requests.post(webhook_url, json={"content": f"❌ {message.author.name} a tenté d'utiliser la commande rmrole sans mentionner d'utilisateur."})
                return
            
            member = message.mentions[0]
            role_id = int(args[2].strip('<@&>'))
            role = message.guild.get_role(role_id)
            
            if role is None:
                await message.channel.send(f"❌ Le rôle '{role_id}' n'existe pas")
                return
            
            # Retirer le rôle du membre
            await member.remove_roles(role)
            await message.channel.send(f"✅ Le rôle '@{role.name}' a été retiré de {member.name}")
            requests.post(webhook_url, json={"content": f"✅ {message.author.name} a retiré le rôle '@{role.name}' de {member.name}"})
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de retirer ce rôle")
            requests.post(webhook_url, json={"content": f"❌ {message.author.name} a tenté d'utiliser la commande rmrole mais le bot n'a pas les permissions nécessaires."})
        except Exception as e:
            await message.channel.send(f"❌ Une erreur s'est produite: {str(e)}")
                             
    if message.content.startswith('!getrole'):
            args = message.content.split()
            if len(args) < 2:
                await message.channel.send("❌ Usage: !getrole <nom_du_rôle>")
                return
            role_name = args[1]
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role is None:
                await message.channel.send(f"❌ Le rôle '{role_name}' n'existe pas.")
                return
            try:
                channel = client.get_channel(1450074107319423050)
                await channel.send(f" L'utilisateur @{message.author.name} a demandé le rôle '{role_name}'.")
                await message.channel.send(f"✅ Votre demande pour le rôle '{role_name}' a été envoyée aux STAFF du serveur.")
            except discord.Forbidden:
                await message.channel.send("❌ Je n'ai pas la permission d'ajouter ce rôle.")
        
    if message.content.startswith('!recolte'):
        args = message.content.split(" ", 1)
        if len(args) < 2:
            await message.channel.send("❌ Usage: !recolte <type_de_culture>")
            return
        crop_type = args[1].lower()
        info = get_recolte_info(crop_type)
        # renvoyer le message en DM à l'utilisateur
        await message.author.send(info)
        await message.channel.send("✅ Les informations de récolte vous ont été envoyées en message privé.", delete_after=10)
        # delete the command message to keep the channel clean
        await message.delete()
        
    
        
    
        
        
        

def new_func(message, role_name):
    role = discord.utils.get(message.guild.roles, name=role_name)
    return role


        
client.run(os.getenv('Token'))

app.run(host=HOST, port=PORT)