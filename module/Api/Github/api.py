import requests
import json


url = 'https://api.github.com/repos/alexcaussades/FarmingBot/releases/latest'


def get_latest_release():
    response = requests.get(url)
    data = response.json()
    return data.get('tag_name')

