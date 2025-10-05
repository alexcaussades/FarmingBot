import json
import os

class TaskManager:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_tasks(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=4)

    def add_task(self, description, member, mois, player_name):
        task = {
            "description": description.strip(),
            "mois": mois.strip(),
            "players": [
                {"id": member, "name": player_name}
            ],
            "status": "pending"
        }
        self.tasks.append(task)
        self.save_tasks()
        return task

    def get_tasks(self):
        return self.tasks

    def update_task_status(self, index, status):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["status"] = status
            self.save_tasks()
            return True
        return False

    def remove_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.save_tasks()
            return True
        return False