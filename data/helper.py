import csv
import time

def add_timestamps_to_seen_post_ids(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    current_time = time.time()
    for i, row in enumerate(rows):
        if i < 100:
            timestamp = current_time - 86400  # 24 hours
        else:
            timestamp = current_time - 57600  # 16 hours
        rows[i] = [row[0], str(timestamp)]

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

add_timestamps_to_seen_post_ids('data/seen_post_ids.csv')