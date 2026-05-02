import csv


def import_tasks_from_csv(path):
    class Task:
        pass

    tasks = []
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            task = Task()
            task.id = int(row["id"])
            task.description = row["description"]
            tasks.append(task)
    return tasks
