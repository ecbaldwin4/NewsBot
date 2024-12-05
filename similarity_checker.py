import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv
import time

HEADLINES = 'data/headlines.csv'
SIMILARITY_THRESHOLD = 0.83

def is_csv_file_empty(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        return sum(1 for _ in reader) == 0
    
def read_csv(filename):
    data = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            headline = row[0]
            timestamp = float(row[1])
            data.append((headline, timestamp))
    return data

def insert_headline(filename, headline):
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        timestamp = time.time()
        writer.writerow([headline, timestamp])

def remove_old_headlines(filename):
    current_time = time.time()
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = [row for row in reader if current_time - float(row[1]) < 172800]  # 172800 seconds in 48 hours
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def headline_is_similar(headline):
    remove_old_headlines(HEADLINES)
    if is_csv_file_empty(HEADLINES):
        insert_headline(HEADLINES, headline)
    else:
        headlines = read_csv(HEADLINES)
        encoded_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{headline}")
        encoded_headline = np.array(encoded_headline['embedding']).reshape(1,-1)
        for hd in headlines:
            compare_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{hd[0]}")
            compare_headline = np.array(compare_headline['embedding']).reshape(1,-1)
            similarity = cosine_similarity(encoded_headline, compare_headline)
            if similarity > SIMILARITY_THRESHOLD:
                print(headline, "::", hd)
                print("Not posting. Too similar: ", similarity)
                return False
        insert_headline(HEADLINES, headline)
        print(headline)
        print("Posting.")
    return True