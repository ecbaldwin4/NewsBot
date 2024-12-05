import csv
import json
import random
import requests
import time

class NewsFeed:
    def __init__(self, post_ids_file="data/seen_post_ids.csv", sources_file="data/sources.csv"):
        self.post_ids_file = post_ids_file
        self.sources_file = sources_file
        self.seen_post_ids = self.load_seen_post_ids()
        self.sources = self.load_sources()

    def load_seen_post_ids(self):
        try:
            with open(self.post_ids_file, "r") as file:
                reader = csv.reader(file)
                seen_post_ids = {}
                for row in reader:
                    post_id, timestamp = row
                    seen_post_ids[post_id] = float(timestamp)
                return seen_post_ids
        except FileNotFoundError:
            return {}

    def save_seen_post_ids(self):
        with open(self.post_ids_file, "w", newline="") as file:
            writer = csv.writer(file)
            current_time = time.time()
            for post_id, timestamp in self.seen_post_ids.items():
                if current_time - timestamp < 86400:  # 86400 seconds in 24 hours
                    writer.writerow([post_id, timestamp])

    def has_seen_post(self, post_id):
        return post_id in self.seen_post_ids

    def mark_post_as_seen(self, post_id):
        self.seen_post_ids[post_id] = time.time()
        self.save_seen_post_ids()

    def load_sources(self):
        sources = {}
        with open(self.sources_file, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                author, json_url = row
                sources[json_url] = author
        return sources

    def get_random_source(self):
        return random.choice(list(self.sources.items()))
    
    def get_latest_post_from_any_source(self):
        # Create a copy of the sources list and shuffle it
        shuffled_sources = list(self.sources.items())
        random.shuffle(shuffled_sources)

        for json_url, author in shuffled_sources:
            latest_post = self.get_latest_post(json_url, author)
            if latest_post:
                print(f"Latest post found from {json_url}")
                return latest_post

        return None

    def get_latest_post(self, json_url, author):
        # Load banned keywords from CSV
        banned_keywords = set()
        with open('data/banned_keywords.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                banned_keywords.update(row)

        headers = {"User-Agent": "news_feed_monitor"}
        response = requests.get(json_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None

        try:
            data = json.loads(response.text)
            posts = data["data"]["children"]

            # Calculate the threshold timestamp for posts older than 24 hours
            threshold_timestamp = int(time.time()) - 86400

            for post in posts:
                post_id = post["data"]["id"]
                title = post["data"]["title"]
                url = post["data"].get("url_overridden_by_dest", post["data"].get("url", ""))
                created_utc = post["data"]["created_utc"]
                post_author = post["data"]["author"]

                if created_utc < threshold_timestamp:
                    continue  # Skip posts older than 24 hours

                if author == "any" or post_author == author:
                    if not url:  # Check if the post has a URL
                        self.mark_post_as_seen(post_id)  # Mark as seen and skip
                        continue

                    # Check if the URL contains any banned keywords
                    if any(keyword.lower() in url.lower() for keyword in banned_keywords):
                        self.mark_post_as_seen(post_id)  # Mark as seen but don't return
                        continue

                    if not self.has_seen_post(post_id):
                        self.mark_post_as_seen(post_id)
                        return title, url

            return None

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return None

        except KeyError as e:
            print(f"Missing key in JSON data: {e}")
            return None