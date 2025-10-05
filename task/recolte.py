import json
import os

class recolte:
    def __init__(self, type, semis, recolte):
        self.type = type
        self.semis = semis
        self.recolte = recolte

dict_recolte = {
    "herbe": recolte("herbe", "Mars, Avril, Mai, Juin, Juillet, Aout, Septembre, Octobre, Novembre", "Tous les mois"),
    "betterave": recolte("betterave", "Avril, Mai, Juin", "Aout, Septembre, Octobre, Novembre"),
    "betterave sucrière": recolte("betterave sucrière", "Mars, Avril", "Octobre, Novembre"),
    "ble": recolte("blé", "Septembre, Octobre", "Juillet, Aout N+1"),
    "canne à sucre": recolte("canne à sucre", "Mars, Avril", "Octobre, Novembre"),
    "colza": recolte("colza", "Août, Septembre", "Juillet, Aout N+1"),
    "coton": recolte("coton", "Février, Mars", "Octobre, Novembre"),
    "couvert végétal": recolte("couvert végétal", "Mars, Avril, Mai, Juin, Juillet, Aout, Septembre, Octobre, Novembre", "Tous les mois"),
    "haricot vert": recolte("haricot vert", "Avril, Mai, Juin", "Août, Septembre, Octobre, Novembre"),
    "luzerne": recolte("luzerne", "Mars, Avril, Mai, Juin, Juillet, Aout, Septembre, Octobre, Novembre", "Tous les mois"),
    "maïs": recolte("maïs", "Avril, Mai", "Septembre, Octobre, Novembre"),
    "moutarde": recolte("moutarde", "Août, Septembre", "Juillet, Aout N+1"),
    "olives": recolte("olives", "Mars, Avril, Mai, Juin", "Octobre"),
    "orge": recolte("orge", "Septembre, Octobre", "Juin, Juillet N+1"),
    "panais": recolte("panais", "Avril, Mai, Juin", "Aout, Septembre, Octobre, Novembre"),
    "petit pois": recolte("petit pois", "Mars, Avril", "Aout, Septembre"),
    "pommes de terre": recolte("pommes de terre", "Mars, Avril", "Aout, Septembre"),
    "radis": recolte("radis", "Mars, Avril, Mai, Juin, Juillet, Aout, Septembre, Octobre, Novembre", "Tous les mois"),
    "raisin": recolte("raisin", "Mars, Avril, Mai", "Septembre, Octobre"),
    "riz": recolte("riz", "Avril, Mai", "Août, Septembre"),
    "riz long grain": recolte("riz long grain", "Avril", "Septembre"),
    "soja": recolte("soja", "Avril, Mai", "Octobre, Novembre"),
    "sorgo": recolte("sorgo", "Avril, Mai", "Août, Septembre"),
    "tournesol": recolte("tournesol", "Mars, Avril", "Octobre, Novembre"),
    "epinard": recolte("épinard", "Mars, Avril, Mai", "juin, Juillet, Aout, Septembre, Octobre, Novembre"),
}


def get_recolte_info(crop_type):
        if crop_type in dict_recolte:
            recolte_info = dict_recolte[crop_type]
            return f"Type: {recolte_info.type}\nSemis: {recolte_info.semis}\nRécolte: {recolte_info.recolte}"
        else:
            return "Type de culture non trouvé. Veuillez vérifier l'orthographe."

def list_crops():
    return ", ".join(dict_recolte.keys())

def add_crop(type, semis, recolte):
    type = type.lower()
    if type in dict_recolte:
        return f"La culture '{type}' existe déjà."
    else:
        dict_recolte[type] = recolte(type, semis, recolte)
        return f"Culture '{type}' ajoutée avec succès."


    