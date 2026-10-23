import os
import asyncio
import requests
import discord
from discord import app_commands
from dotenv import load_dotenv
from pathlib import Path

from module.Api.farming import FarmingAPI
from module.Api.tasks import TasksAPI
from module.recolte.recolte import get_recolte_info
from module.Api.Github.api import get_latest_release

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
app_env = os.environ.get("APP_ENV", "web").lower()
env_file = Path(__file__).resolve().parent / f".env.{app_env}"
load_dotenv(env_file, override=False)

TOKEN = os.getenv("Token")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
API_URL = os.getenv("API_URL")
# ------------------------------------------------------------
# Arborescence slash : /fs25 ...
# ------------------------------------------------------------
fs25 = app_commands.Group(
    name="fs25",
    description="Toutes les commandes Farming Simulator 25"
)

parcelle = app_commands.Group(
    name="parcelle",
    description="Recherche et réservation des parcelles"
)
tache = app_commands.Group(
    name="tache",
    description="Gestion des tâches agricoles"
)
culture = app_commands.Group(
    name="culture",
    description="Informations sur les cultures"
)
serveur = app_commands.Group(
    name="serveur",
    description="État du serveur Farming Simulator 25"
)

# ------------------------------------------------------------
# Arborescence slash : /fs25 ...
# ------------------------------------------------------------
infoivao = app_commands.Group(
    name="ivao",
    description="Commandes liées à IVAO"
)

metar = app_commands.Group(
    name="metar",
    description="Obtenir le METAR d'un aéroport"
)

atc = app_commands.Group(
    name="atc",
    description="Obtenir les informations ATC d'un aéroport"
)

taf = app_commands.Group(
    name="taf",
    description="Obtenir le TAF d'un aéroport"
)

fs25.add_command(parcelle)
fs25.add_command(tache)
fs25.add_command(culture)
fs25.add_command(serveur)
tree.add_command(fs25)
tree.add_command(infoivao)




async def send_private_result(interaction: discord.Interaction, content: str):
    """Répond en privé dans l'interaction Discord."""
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=True)
    else:
        await interaction.response.send_message(content, ephemeral=True)

# ------------------------------------------------------------
# /ivao information sur IVAO
# ------------------------------------------------------------
@infoivao.command(name="metar", description="Obtenir le METAR d'un aéroport")
@app_commands.describe(icao="Code ICAO de l'aéroport")
async def metar(interaction: discord.Interaction, icao: str):
    await interaction.response.defer(ephemeral=True)
    try:
        response = requests.get(f"{API_URL}/ivao/metar/{icao}")
        if response.status_code == 200:
            data = response.json()
            await interaction.followup.send(f" METAR : {data['data']['metar']} \nLa dernière mise à jour date de {data['data']['update']} l'observation", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Aucune information METAR trouvée pour **{icao}**.", ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)

@infoivao.command(name="taf", description="Obtenir le TAF d'un aéroport")
@app_commands.describe(icao="Code ICAO de l'aéroport")
async def taf(interaction: discord.Interaction, icao: str):
    await interaction.response.defer(ephemeral=True)
    try:
        response = requests.get(f"{API_URL}/ivao/taf/{icao}")
        if response.status_code == 200:
            data = response.json()
            await interaction.followup.send(f" TAF : {data['data']['taf']} \nLa dernière mise à jour date de {data['data']['update']} l'observation", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Aucune information TAF trouvée pour **{icao}**.", ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)

@infoivao.command(name="atc", description="Obtenir les informations ATC d'un aéroport")
@app_commands.describe(icao="Code ICAO de l'aéroport")
async def atc(interaction: discord.Interaction, icao: str):
    dict_atc = {
        "A" : "ALPHA",
        "B" : "BRAVO",
        "C" : "CHARLIE",
        "D" : "DELTA",
        "E" : "ECHO",
        "F" : "FOXTROT",
        "G" : "GOLF",
        "H" : "HOTEL",
        "I" : "INDIA",
        "J" : "JULIET",
        "K" : "KILO",
        "L" : "LIMA",
        "M" : "MIKE",
        "N" : "NOVEMBER",
        "O" : "OSCAR",
        "P" : "PAPA",
        "Q" : "QUEBEC",
        "R" : "ROMEO",
        "S" : "SIERRA",
        "T" : "TANGO",
        "U" : "UNIFORM",
        "V" : "VICTOR",
        "W" : "WHISKEY",
        "X" : "X-RAY",
        "Y" : "YANKEE",
        "Z" : "ZULU"
    }
    await interaction.response.defer(ephemeral=True)
    try:
        response = requests.get(f"{API_URL}/ivao/atis/{icao}")
        if response.status_code == 200:
            data = response.json()
            await interaction.followup.send(f" Informations **{dict_atc[data['data']['revision']]}**\n{data['data']['information']} \nLa dernière mise à jour date de {data['data']['update']} la publication", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Aucune information ATC trouvée pour **{icao}**.", ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 parcelle rechercher
# ------------------------------------------------------------
@parcelle.command(name="rechercher", description="Rechercher une parcelle par son ID")
@app_commands.describe(id="Identifiant de la parcelle")
async def parcelle_rechercher(interaction: discord.Interaction, id: str):
    await interaction.response.defer(ephemeral=True)
    try:
        api = FarmingAPI()
        data = await asyncio.to_thread(api.get_serveur_farming_parcels, id)
        if data:
            await interaction.followup.send(
                f"ℹ️ Informations de la parcelle **{id}** :\n```{data}```",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Aucune information trouvée pour la parcelle `{id}`.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 parcelle reserver
# ------------------------------------------------------------
@parcelle.command(name="reserver", description="Réserver une parcelle")
@app_commands.describe(id="Identifiant de la parcelle à réserver")
async def parcelle_reserver(interaction: discord.Interaction, id: str):
    await interaction.response.defer(ephemeral=True)
    try:
        api = FarmingAPI()
        payload = {"user_id": interaction.user.id}
        data = await asyncio.to_thread(api.push_reservation, id, payload)
        if data:
            await interaction.followup.send(
                f"✅ {interaction.user.mention}, la parcelle **{id}** a été réservée.\n"
                f"Pour annuler : `/fs25 parcelle annuler` avec l'ID `{id}`.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Impossible de réserver la parcelle `{id}`.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 parcelle annuler
# ------------------------------------------------------------
@parcelle.command(name="annuler", description="Annuler sa réservation d'une parcelle")
@app_commands.describe(id="Identifiant de la parcelle")
async def parcelle_annuler(interaction: discord.Interaction, id: str):
    await interaction.response.defer(ephemeral=True)
    try:
        api = FarmingAPI()
        payload = {"user_id": interaction.user.id}
        data = await asyncio.to_thread(api.cancel_reservation, id, payload)
        if data:
            await interaction.followup.send(
                f"✅ Réservation de la parcelle **{id}** annulée.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Impossible d'annuler la réservation de `{id}`.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 parcelle verifier
# ------------------------------------------------------------
@parcelle.command(name="verifier", description="Vérifier une parcelle et sa réservation")
@app_commands.describe(id="Identifiant de la parcelle")
async def parcelle_verifier(interaction: discord.Interaction, id: str):
    await interaction.response.defer(ephemeral=True)
    try:
        api = FarmingAPI()
        data = await asyncio.to_thread(api.get_serveur_farming_parcels, id)
        if data:
            await interaction.followup.send(
                f"ℹ️ Résultat pour la parcelle **{id}** :\n```{data}```",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Aucune information trouvée pour `{id}`.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 tache mois
# ------------------------------------------------------------
@tache.command(name="mois", description="Afficher les tâches d'un mois")
@app_commands.describe(mois="Numéro du mois (1 à 12) ou nom du mois")
async def tache_mois(interaction: discord.Interaction, mois: str):
    await interaction.response.defer(ephemeral=True)
    mapping = {
        "1": "janvier", "2": "février", "3": "mars", "4": "avril",
        "5": "mai", "6": "juin", "7": "juillet", "8": "août",
        "9": "septembre", "10": "octobre", "11": "novembre", "12": "décembre"
    }
    try:
        api = TasksAPI()
        data = await asyncio.to_thread(api.get_tasks_by_month, mois)
        mois_affiche = mapping.get(mois, mois)
        if data:
            await interaction.followup.send(
                f"📅 **Tâches pour {mois_affiche}**\n```{data}```",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"ℹ️ Aucune tâche trouvée pour **{mois_affiche}**.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 tache creer
# ------------------------------------------------------------
@tache.command(name="creer", description="Créer une tâche pour une parcelle")
@app_commands.describe(
    parcelle_id="Identifiant numérique de la parcelle",
    nom="Nom de la tâche à effectuer",
    mois="Mois concerné (numéro ou nom)"
)
async def tache_creer(
    interaction: discord.Interaction,
    parcelle_id: int,
    nom: str,
    mois: str
):
    await interaction.response.defer(ephemeral=True)
    try:
        api = TasksAPI()
        task_data = {
            "player_id": str(interaction.user.id),
            "farmland_id": parcelle_id,
            "task_name": nom,
            "month": mois
        }
        data = await asyncio.to_thread(api.create_task, mois, task_data)
        if data:
            await interaction.followup.send(
                f"✅ Tâche créée pour la parcelle **{data.get('farmland_id', parcelle_id)}**.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Impossible de créer la tâche pour le mois `{mois}`.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 culture recolte
# ------------------------------------------------------------
@culture.command(name="recolte", description="Obtenir les informations de semis et récolte")
@app_commands.describe(type_culture="Nom de la culture (ex. blé, orge, maïs)")
async def culture_recolte(interaction: discord.Interaction, type_culture: str):
    await interaction.response.defer(ephemeral=True)
    try:
        info = await asyncio.to_thread(get_recolte_info, type_culture.lower())
        await interaction.followup.send(str(info)[:1900], ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# /fs25 serveur uptime
# ------------------------------------------------------------
@serveur.command(name="uptime", description="Vérifier l'état et le temps de fonctionnement du serveur")
async def serveur_uptime(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        api = FarmingAPI()
        data = await asyncio.to_thread(api.uptime)
        if data:
            await interaction.followup.send(f"🟢 **État du serveur FS25**\n{data}", ephemeral=True)
        else:
            await interaction.followup.send(
                "❌ Impossible de récupérer l'état du serveur.",
                ephemeral=True
            )
    except Exception as exc:
        await interaction.followup.send(f"❌ Erreur API : `{exc}`", ephemeral=True)


# ------------------------------------------------------------
# Événements Discord
# ------------------------------------------------------------
@client.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"Connecté en tant que {client.user}")
        print(f"{len(synced)} commande(s) slash synchronisée(s).")
        message = os.getenv("MessageServeur", "Farming Simulator 25 ")
        version = get_latest_release()
        await client.change_presence(
            activity=discord.Game(name=f"{message} V{version}")
        )
        if WEBHOOK_URL:
            requests.post(
                WEBHOOK_URL,
                json={"content": f"🤖 Bot connecté : {client.user}"},
                timeout=5
            )
    except Exception as exc:
        print(f"Erreur au démarrage : {exc}")


@client.event
async def on_member_join(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name="Membres")
    if role:
        try:
            await member.add_roles(role, reason="Attribution automatique à l'arrivée")
        except discord.Forbidden:
            print(f"Permission insuffisante pour attribuer Membres à {member}")
    else:
        print("Le rôle 'Membres' n'existe pas.")


@client.event
async def on_message_delete(message: discord.Message):
    if message.author == client.user or not WEBHOOK_URL:
        return
    requests.post(
        WEBHOOK_URL,
        json={"content": f"🗑️ Message supprimé de {message.author}: {message.content[:500]}"},
        timeout=5
    )


@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author == client.user or before.content == after.content or not WEBHOOK_URL:
        return
    requests.post(
        WEBHOOK_URL,
        json={
            "content": (
                f"✏️ {before.author} a modifié un message dans #{before.channel}.\n"
                f"Avant : {before.content[:400]}\nAprès : {after.content[:400]}"
            )
        },
        timeout=5
    )


# ------------------------------------------------------------
# Anciennes commandes préfixées conservées
# !bonjour et !recolte restent disponibles.
# La modération !purge / !kick / !addrole / !rmrole / !getrole
# peut rester dans un module séparé et être migrée ensuite.
# ------------------------------------------------------------
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.content.startswith("!bonjour"):
        staff_role = discord.utils.get(message.guild.roles, name="STAFF") if message.guild else None
        if staff_role and staff_role in getattr(message.author, "roles", []):
            await message.channel.send(f"Bonjour {message.author.mention}, voici l'un de mes maîtres.")
        else:
            await message.channel.send(f"Bonjour {message.author.mention} ! 👋")

    elif message.content.startswith("!recolte"):
        parts = message.content.split(maxsplit=1)
        if len(parts) < 2:
            await message.channel.send("❌ Utilisation : `!recolte <type_de_culture>`")
            return
        try:
            info = await asyncio.to_thread(get_recolte_info, parts[1].lower())
            await message.author.send(str(info)[:1900])
            await message.channel.send(
                "✅ Les informations de récolte ont été envoyées en message privé.",
                delete_after=10
            )
            await message.delete()
        except discord.Forbidden:
            await message.channel.send("❌ Je ne peux pas vous envoyer de message privé.")

    # Les commandes de modération préfixées doivent être réintégrées ici
    # ou, de préférence, déplacées vers un Cog/module dédié.


if not TOKEN:
    raise RuntimeError("La variable Token est absente du fichier .env.")

client.run(TOKEN)
