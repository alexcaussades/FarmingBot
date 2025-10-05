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

connect_db()

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
        response = requests.get(Serveur_info_live)
        with open("serveur.xml", "wb") as file:
            file.write(response.content)
        tree = ET.parse('serveur.xml')
        root = tree.getroot()
        server_name = root.get('name')
        await message.channel.send('Bonjour ' + message.author.name + ' ! \n je suis le bot du serveur ' + server_name + ' ! \n Pour voir les commandes disponibles, tapez !help')

    if message.content.startswith('!help'):
        await message.channel.send("Voici les commandes disponibles : \n !bonjour,\n !serveur,\n !players,\n !addtask,\n !listtasks,\n !updatetask,\n !removetask,\n !mouthtask,\n !task-help \n !recolte")

    if message.content.startswith('!serveur'):
        response = requests.get(Serveur_info_live)
        with open("serveur.xml", "wb") as file:
            file.write(response.content)
        tree = ET.parse('serveur.xml')
        root = tree.getroot()
        response2 = requests.get(Serveur_carriere_live)
        with open("carriere.xml", "wb") as file:
            file.write(response2.content)
        tree2 = ET.parse('carriere.xml')
        root2 = tree2.getroot()
        server_name = root.get('name')
        player_count = root.find('Slots').get('numUsed')
        Autosave = root2.find('settings').find('autoSaveInterval').text
        Autosave = Autosave.split('.')[0]
        TimeScale = root2.find('settings').find('timeScale').text
        TimeScale1 = TimeScale.split('.')[0]
        TimeScale2 = TimeScale.split('.')[1][:-5]
        if TimeScale2 == '0':
            TimeScale = TimeScale1
        else:
            TimeScale = TimeScale1 + ',' + TimeScale2
        disasterDestructionState = root2.find('settings').find('disasterDestructionState').text
        if disasterDestructionState == 'ENABLED':
            disasterDestructionState = 'Activé'
        else:
            disasterDestructionState = 'Désactivé'
        TimePlay = root2.find("statistics").find("playTime").text
        TimePlay = TimePlay.split('.')[0]
        TimePlay = int(TimePlay)
        hours = TimePlay // 60
        minutes = TimePlay % 60
        TimePlay = f"{hours} heures et {minutes} minutes"
        await message.channel.send(f"Nom du serveur : {server_name}\nNombre de joueurs : {player_count}\nAutosave : {Autosave} Minutes\nVitesse : {TimeScale}\nÉtat de destruction des cultures : {disasterDestructionState} \nTemps de jeu total : {TimePlay}")

    if message.content.startswith('!players'):
        response = requests.get(Serveur_info_live)
        with open("serveur.xml", "wb") as file:
            file.write(response.content)
        tree = ET.parse('serveur.xml')
        root = tree.getroot()
        players = root.find('Slots').findall('Player')
        if not players or all(player.get('isUsed') == 'false' for player in players):
            await message.channel.send("Aucun joueur n'est connecté.")
            return
        player_names = [player.text for player in players if player.get('isUsed') == 'true']
        await message.channel.send(f"Joueurs connectés : {', '.join(player_names)}")

    if message.content.startswith('!addtask'):
        parts = message.content.split(' ', 3)
        if len(parts) < 3:
            await message.channel.send("Usage: !addtask <description> <mois> | ex: !addtask maïs aout | !task-help")
            return
        description, mois = parts[1], parts[2]
        task_manager = TaskManager()
        author_name = message.author.name
        task = task_manager.add_task(description, member, mois , author_name)
        await message.channel.send(f"Tâche ajoutée : {author_name} pour {description} en {mois.strip()}")

    if message.content.startswith('!listtasks'):
        task_manager = TaskManager()
        tasks = task_manager.get_tasks()
        if not tasks:
            await message.channel.send("Aucune tâche disponible.")
            return
        response = "Tâches:\n"
        for i, task in enumerate(tasks):
            response += f"{i}. {task['description']} (Mois: {task['mois']}, Joueurs: {task['players'][0]['name']}, Statut: {task['status']})\n"
        await message.channel.send(response)
        
    if message.content.startswith('!updatetask'):
        parts = message.content.split(' ', 2)
        if len(parts) < 3:
            await message.channel.send("Usage: !updatetask <index> <status>")
            return
        try:
            index = int(parts[1])
            status = parts[2]
        except ValueError:
            await message.channel.send("Index invalide. Veuillez fournir un nombre entier.")
            return
        task_manager = TaskManager()
        if task_manager.update_task_status(index, status):
            await message.channel.send(f"Tâche {index} mise à jour avec le statut '{status}'.")
        else:
            await message.channel.send("Index de tâche invalide.")
            
    if message.content.startswith('!removetask'):
        parts = message.content.split(' ', 1)
        if len(parts) < 2:
            await message.channel.send("Usage: !removetask <index>")
            return
        try:
            index = int(parts[1])
        except ValueError:
            await message.channel.send("Index invalide. Veuillez fournir un nombre entier.")
            return
        task_manager = TaskManager()
        if task_manager.remove_task(index):
            await message.channel.send(f"Tâche {index} supprimée.")
        else:
            await message.channel.send("Index de tâche invalide.")
            
    if message.content.startswith('!mouthtask'):
        parts = message.content.split(' ', 1)
        if len(parts) < 2:
            await message.channel.send("Usage: !mouthtask <mois>")
            return
        mois = parts[1].strip()
        task_manager = TaskManager()
        tasks = task_manager.get_tasks()
        filtered_tasks = [task for task in tasks if task['mois'].lower() == mois.lower()]
        if not filtered_tasks:
            await message.channel.send(f"Aucune tâche trouvée pour le mois: {mois}.")
            return
        response = f"Tâches pour le mois de {mois}:\n"
        for i, task in enumerate(filtered_tasks):
            response += f"{i}. {task['description']} (Joueurs: {task['players'][0]['name']}, Statut: {task['status']})\n"
        await message.channel.send(response)
            
    if message.content.startswith('!task-help'):
        help_message = (
            "Commandes de gestion des tâches:\n"
            "!addtask <description> <mois> - Ajouter une nouvelle tâche.\n"
            "!listtasks - Lister toutes les tâches.\n"
            "!mouthtask <mois> - Lister les tâches pour un mois spécifique.\n"
            "!updatetask <index> <status> - Mettre à jour le statut d'une tâche.\n"
            "!removetask <index> - Supprimer une tâche.\n"
            "!task-help - Afficher ce message d'aide."
        )
        await message.channel.send(help_message)

    if message.content.startswith('!recolte'):
        parts = message.content.split(' ', 1)
        if len(parts) < 2:
            await message.channel.send("Usage: !recolte <type_de_culture> | ex: !recolte maïs | !recolte list | !recolte add <type> <semis> <recolte>")
            return
        crop_type = parts[1].strip()
        if crop_type.lower() == "help":
            help_message = (
                "Commandes de gestion des récoltes:\n"
                "!recolte <type_de_culture> - Obtenir les informations de semis et récolte pour une culture spécifique.\n"
                "!recolte list - Lister tous les types de cultures disponibles.\n"
                "!recolte add <type> <semis> <recolte> - Ajouter une nouvelle culture.\n"
                "!recolte help - Afficher ce message d'aide."
            )
            await message.channel.send(help_message)
            return
        if crop_type.lower() == "list":
            crops = list_crops()
            await message.channel.send(f"Types de cultures disponibles : {crops}")
        elif crop_type.lower().startswith("add "):
            add_parts = crop_type.split(' ', 3)
            if len(add_parts) < 4:
                await message.channel.send("Usage: !recolte add <type> <semis> <recolte>")
                return
            _, type, semis, recolte = add_parts
            result = add_crop(type, semis, recolte)
            await message.channel.send(result)
        else:
            info = get_recolte_info(crop_type[0:].strip())
            await message.channel.send(info)
    
        
client.run(os.getenv('Token'))