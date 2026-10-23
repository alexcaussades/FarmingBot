# GameHub (BOT)

Bot Discord pour gérer les parcelles d’un serveur de farming, consulter les tâches agricoles et fournir des informations sur les cultures. Il inclut aussi quelques commandes de modération.

# Fonctionnalités

## Farming

- `/FS25 search <id>` : affiche les informations d’une parcelle.
- `/FS25 check <id>` : consulte les informations de la parcelle, dont son statut et une éventuelle réservation.
- `/FS25 reserve <id>` : réserve une parcelle au nom de votre compte Discord.
- `/FS25 cancel <id>` : annule votre réservation.
- `/FS25 uptime` : affiche l’état du serveur, sa durée de fonctionnement, le nombre de joueurs et l’état de l’API.

### Tâches

- `/FS25 task_for_month <mois>` : liste les tâches d’un mois. Le mois peut être indiqué par son numéro (`1` à `12`) ou son nom.
- `/FS25 create_task <parcelle> <tâche> <mois>` : crée une tâche associée à votre compte Discord.


## Ivao

- `/ivao metar` : Affiche le METAR
- `/ivao taf` : Affiche le TAF
- `/ivao atc` : Affiche les données de ATC


## Cultures et modération

- `!recolte <culture>` : envoie en message privé les périodes de semis et de récolte.
- `!bonjour` et `!help` : salutation et liste des commandes préfixées.
- `!purge <nombre>` : supprime de 1 à 100 messages (rôle `STAFF` ou `VIP`).
- `!kick @utilisateur [raison]` : expulse un membre (rôle `STAFF` ou `VIP`).
- `!addrole @utilisateur @rôle` et `!rmrole @utilisateur @rôle` : attribue ou retire un rôle (rôle `STAFF`).
- `!getrole <nom_du_rôle>` : transmet une demande de rôle au canal configuré dans le code.

Les commandes avec préfixe sont écrites avec `!`. Les commandes de parcelles, tâches et disponibilité sont des commandes slash.
