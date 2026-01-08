from ast import Not
import discord
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import requests
import json
from module.task.task import TaskManager
from module.recolte.recolte import get_recolte_info, list_crops, add_crop
from module.mounth.up_mouth import connect_db, close_connection, update_mouth_task, get_mouth_tasks
import sqlite3

load_dotenv()
Serveur_info_live = os.getenv('Serveur_Stats')
Serveur_carriere_live = os.getenv('Serveur_Career')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True


@client.event
async def on_ready():
   print(f"Bot connecté en tant que {client.user}")
   await client.change_presence(activity=discord.Game(name=os.getenv('MessageServeur') + "V" + os.getenv('Version')))
  

@client.event
async def on_message(message):
    member = message.author.id
    
    if message.author == client.user:
        return

    if message.content.startswith('!bonjour'):
        await message.channel.send('Bonjour ' + message.author.name + ' ! \n je suis le bot du serveur ! \n Pour voir les commandes disponibles, tapez !help')

    if message.content.startswith('!help'):
        await message.channel.send("\n Actuellent en maintenance")

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
                return
            
            # Supprimer les messages (amount + 1 pour inclure la commande)
            deleted = await message.channel.purge(limit=amount + 1)
            await message.channel.send(f"✅ {len(deleted) - 1} message(s) supprimé(s)", delete_after=5)
        except ValueError:
            await message.channel.send("❌ Veuillez entrer un nombre valide")
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de supprimer les messages")

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
                return
            
            # Kick le membre
            await member.kick(reason=reason)
            await message.channel.send(f"✅ {member.name} a été kick du serveur. Raison: {reason}")
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de kick ce membre")
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
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission d'ajouter ce rôle")
        except Exception as e:
            await message.channel.send(f"❌ Une erreur s'est produite: {str(e)}")
            
    if message.content.startswith('!removerole'):
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
        except discord.Forbidden:
            await message.channel.send("❌ Je n'ai pas la permission de retirer ce rôle")
        except Exception as e:
            await message.channel.send(f"❌ Une erreur s'est produite: {str(e)}")

def new_func(message, role_name):
    role = discord.utils.get(message.guild.roles, name=role_name)
    return role
    
    
        
client.run(os.getenv('Token'))