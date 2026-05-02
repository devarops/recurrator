import csv
from enum import Enum


class Context(Enum):
    LAPTOP = "laptop"


class Task:
    pass


def import_tasks_from_csv(path):
    tasks = []
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            task = Task()
            task.id = int(row["id"])
            task.description = row["description"]
            task.context = Context(row["context"])
            tasks.append(task)
    return tasks
