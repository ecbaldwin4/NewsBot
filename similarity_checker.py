import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv
import time

HEADLINES = 'data/headlines.csv'

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
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        timestamp = time.time()
        writer.writerow([headline, timestamp])

def headline_is_similar(headline):
    if is_csv_file_empty(HEADLINES):
        insert_headline(HEADLINES, headline)
    else:
        headlines = read_csv(HEADLINES)
        encoded_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{headline}")
        encoded_headline = np.array(encoded_headline['embedding']).reshape(1,-1)
        for hd in headlines:
            compare_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{hd}")
            compare_headline = np.array(compare_headline['embedding']).reshape(1,-1)
            similarity = cosine_similarity(encoded_headline, compare_headline)
            if similarity > 0.6:
                print(headline, "::", hd)
                print("Not posting. Too similar: ", similarity)
                return False
        insert_headline(HEADLINES, headline)
        print(headline)
        print("Posting.")
    return True
            