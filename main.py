import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import requests
import json
import asyncio
from pathlib import Path
from module.Api.farming import FarmingAPI
from module.Api.tasks import TasksAPI
from module.recolte.recolte import get_recolte_info, list_crops, add_crop
from module.mounth.up_mouth import connect_db, close_connection, update_mouth_task, get_mouth_tasks
from module.Api.Github.api import get_latest_release
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================
app_env = os.environ.get("APP_ENV","local").lower()
env_file = Path(__file__).resolve().parent / f".env.{app_env}"
load_dotenv(env_file)

def recharger_env():
    load_dotenv(override=True)

recharger_env()


webhook_url = os.environ.get("DISCORD_WEBHOOK")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_TEST")
URL_TASKS = os.environ.get("URL_TASKS")
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
   print(f"Bot connecté en tant que {client.user}")
   await tree.sync()
   await client.change_presence(activity=discord.Game(name=os.getenv('MessageServeur') + "V" + get_latest_release()))
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
           
    
@tree.command(
    name="search",
    description="Obtenir les informations du parcelle de farming <Parcelle ID>"
)
    
async def search(
    interaction: discord.Interaction,
    id: str
):
    await interaction.response.defer(ephemeral=True)
    try:
        farming_api = FarmingAPI()
        data = await asyncio.to_thread(farming_api.get_serveur_farming_parcels, id)
        if data:
            await interaction.user.send(
                f"✅ Informations du parcelle de farming pour l'ID '{id}': {data}"
            )
        else:
            await interaction.user.send(
                f"❌ Impossible de récupérer les informations du parcelle de farming pour l'ID '{id}'."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

@tree.command(
    name="reserve",
    description="Réserver un parcelle de farming <Parcelle ID>"
)
async def reserve(
    interaction: discord.Interaction,
    id: str,
   
):
    await interaction.response.defer(ephemeral=True)
    try:
        farming_api = FarmingAPI()
        reservation_data = interaction.user.id
        data = await asyncio.to_thread(farming_api.push_reservation, id, {"user_id": reservation_data})
        print(f"Push reservation response: {data}")
        if data:
            await interaction.user.send(
                f"✅ Bravo {interaction.user.mention} ! Tu as bien réservé la parcelle du serveur: {id} \n Pour annuler, utilise la commande /cancel {id}"
            )
        else:
            await interaction.user.send(
                f"❌ Impossible de réserver la parcelle: {id} ."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

@tree.command(
    name="cancel",
    description="Annuler une réservation d'un parcelle de farming <Parcelle ID>"
)
async def cancel(
    interaction: discord.Interaction,
    id: str,
):
    await interaction.response.defer(ephemeral=True)
    try:
        farming_api = FarmingAPI()
        reservation_data = interaction.user.id
        data = await asyncio.to_thread(farming_api.cancel_reservation, id, {"user_id": reservation_data})
        print(f"Cancel reservation response: {data}")
        if data:
            await interaction.user.send(
                f"✅ Bravo {interaction.user.mention} ! Tu as bien annulé la réservation de la parcelle {id} du serveur "
            )
        else:
            await interaction.user.send(
                f"❌ Impossible d'annuler la réservation de la parcelle: {id} ."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

@tree.command(
    name="check",
    description="Vérifier la réservation d'un parcelle de farming <Parcelle ID>"
)
async def check(
    interaction: discord.Interaction,
    id: str,
):
    await interaction.response.defer(ephemeral=True)
    try:
        farming_api = FarmingAPI()
        data = await asyncio.to_thread(farming_api.get_serveur_farming_parcels, id)
        if data:
            await interaction.user.send(
                f"ℹ️ Informations de la parcelle: {id} : {data}"
            )
        else:
            await interaction.user.send(
                f"❌ Impossible de récupérer les informations du parcelle de farming pour l'ID '{id}'."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

@tree.command(
    name='uptime',
    description="Vérifier le temps de fonctionnement du serveur de farming et l'état de l'API"
)
async def uptime(
    interaction: discord.Interaction,
):
    await interaction.response.defer(ephemeral=True)
    try:
        farming_api = FarmingAPI()
        data = await asyncio.to_thread(farming_api.uptime)
        if data:
            await interaction.user.send(
                f"{data}"
            )
        else:
            await interaction.user.send(
                f"❌ Impossible de récupérer le temps de fonctionnement du serveur de farming."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

@tree.command(
    name="task_for_month",
    description="Récupérer les tâches pour le mois <Mois> | Exemple: 1:12 || janvier, février, etc.",
)
async def tasks_by_month(
    interaction: discord.Interaction,
    month: str,
):
    await interaction.response.defer(ephemeral=True)
    try:
        tasks_api = TasksAPI()
        data = await asyncio.to_thread(tasks_api.get_tasks_by_month, month, )
        month_mapping = {
            "1": "janvier",
            "2": "février",
            "3": "mars",
            "4": "avril",
            "5": "mai",
            "6": "juin",
            "7": "juillet",
            "8": "août",
            "9": "septembre",
            "10": "octobre",
            "11": "novembre",
            "12": "décembre"
        }
        if data:
            await interaction.user.send(
                f"ℹ️ Tâches pour le mois {month_mapping.get(month, month)} : {data}"
            )
        else:
            await interaction.user.send(
                f"❌ aucun résultat pour le mois : '{month_mapping.get(month, month)}'."
            )
    except Exception as e:
        await interaction.user.send(
            f"❌ Une erreur s'est produite: {str(e)}"
        )

client.run(os.getenv('Token'))