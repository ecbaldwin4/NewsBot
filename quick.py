import csv
import time

def add_timestamp_to_seen_post_ids(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)
    
    timestamp = int(time.time()) + 54000  # 15 hours in seconds
    
    for row in data:
        row.append(str(timestamp))
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

# Usage
filename = 'seen_post_ids.csv'
add_timestamp_to_seen_post_ids(filename)