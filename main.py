import os
import random
import time
from datetime import datetime
from typing import Dict, Tuple

import requests
from mock import MagicMock
from openai import OpenAI

BANNED_WORDS = ["kill", "suicide", "murder", "hanged"]


def filter_events(event: Dict):
    text = event["text"]
    words = text.lower().split(" ")
    return not any(banned in word for word in words for banned in BANNED_WORDS)


def get_historical_event() -> Tuple[str, str, str]:
    date = datetime.now().strftime("%m/%d")
    year = int(datetime.now().strftime("%Y"))
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{date}"
    api_key = os.environ.get("WIKIMEDIA_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "TootsThroughTheAges",
    }

    got_event = False
    tries = 0
    while not got_event:
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            events = data["events"]
            got_event = True
        except Exception:
            print("Error getting events... Retrying")
            time.sleep(5)
            tries += 1
            if tries >= 5:
                raise RuntimeError("Failed to get events")

    events = [event for event in events if year - int(event["year"]) > 60]
    filtered_events = list(filter(filter_events, events))
    event = random.choice(filtered_events)

    for page in event["pages"]:
        if page["type"] == "standard":
            url = page["content_urls"]["desktop"]["page"]
            break
    return (event["text"], event["year"], url)


def get_toot(event: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a tweet generator for a person from history."
                "The user gives you a historical event, and you generate a satirical tweet from"
                "the perspective of the main person involved. Only respond with the tweet"
                "and the name of the person who would have tweeted it or their title.",
            },
            {"role": "user", "content": event},
        ],
    )
    return res.choices[0].message.content


def post_toot(toot: str, event: str, year: str, page_url: str, mock: bool) -> None:
    date = datetime.now().strftime("%b %d")
    url = "https://techhub.social/api/v1/statuses"

    api_key = os.environ.get("MASTODON_API_KEY")
    auth = {"Authorization": f"Bearer {api_key}"}

    params = {"status": f"{toot}\n\n{date}, {year} - {event}\n{page_url}"}

    if not mock:
        requests.post(url, headers=auth, data=params)
    else:
        print(params)


def main(context, mock: bool = False):
    event, year, url = get_historical_event()
    context.log(f"Got historical event")
    toot = get_toot(event)
    context.log("Got toot")
    post_toot(toot, event, year, url, mock)
    context.log("Posted toot")

    return context.res.empty()


if __name__ == "__main__":
    context = MagicMock()
    context.log = print
    main(context, True)
