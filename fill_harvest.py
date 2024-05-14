from dotenv import load_dotenv
import argparse
import os
import requests
import logging
import datetime

BASE_URL = "https://api.harvestapp.com/api/v2/"


def headers() -> dict:
    account_id = os.environ["ACCOUNT_ID"]
    api_token = os.environ["API_TOKEN"]
    return {"Harvest-Account-ID": account_id, "Authorization": f"Bearer {api_token}"}


def get(url: str):
    url = f"{BASE_URL}{url}"
    logging.info(f"Get: {url}")
    response = requests.get(url, headers=headers())
    if response.status_code != 200:
        raise Exception(f"non 200 status: {response.json()}")
    return response.json()


def post(url: str, body: dict):
    url = f"{BASE_URL}{url}"
    logging.info(f"Post: {url}")
    response = requests.post(url, data=body, headers=headers())
    if response.status_code != 201:
        raise Exception(f"non 201 status: {response.json()}")
    return response.json()


def get_user_id() -> int:
    response = get("users/me.json")
    return response["id"]


def get_project_assignments() -> dict:
    response = get("users/me/project_assignments")
    return response


def fill_weeks(
    user_id: int, project_id: int, task_id: int, start: int, end: int, weekly_hours: int
):
    logging.info("filling weeks")
    for w in range(start, end + 1):
        fill_week(user_id, project_id, task_id, w, weekly_hours)


def fill_week(
    user_id: int, project_id: int, task_id: int, week: int, weekly_hours: int
):
    logging.info(f"filling week {week} with {weekly_hours} hours")
    daily_hours = weekly_hours / 5

    start_date = datetime.date.fromisocalendar(datetime.date.today().year, week, 1)

    for i in range(5):
        body = {
            "user_id": user_id,
            "project_id": project_id,
            "task_id": task_id,
            "spent_date": (start_date + datetime.timedelta(days=i)).isoformat(),
            "hours": round(daily_hours, 2),
        }
        logging.info(f"sending {body['hours']} hours for date {body['spent_date']}")
        post("time_entries", body=body)


def main():
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("weekly_hours", type=int)
    parser.add_argument("project_name")
    parser.add_argument("task_name")
    parser.add_argument("start_week", type=int)
    parser.add_argument("end_week", type=int)

    args = parser.parse_args()

    user_id = get_user_id()
    project_assignments = get_project_assignments()
    project = next(
        (
            p
            for p in project_assignments["project_assignments"]
            if p["project"]["name"] == args.project_name and p["is_active"]
        ),
        None,
    )
    if project is None:
        projects = [
            p["project"]["name"]
            for p in project_assignments["project_assignments"]
            if p["is_active"]
        ]
        logging.error(f"Couldn't find project, available project: {projects}")
        return

    task = next(
        (
            t
            for t in project["task_assignments"]
            if t["task"]["name"] == args.task_name and t["is_active"]
        ),
        None,
    )
    if task is None:
        tasks = [
            t["task"]["name"] for t in project["task_assignments"] if t["is_active"]
        ]
        logging.error(f"Couldn't find task, available tasks: {tasks}")
        return

    fill_weeks(
        user_id,
        project["project"]["id"],
        task["task"]["id"],
        args.start_week,
        args.end_week,
        args.weekly_hours,
    )


if __name__ == "__main__":
    main()
