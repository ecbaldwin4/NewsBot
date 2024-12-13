import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv
import time

SIMILARITY_THRESHOLD = 0.83

class HeadlineManager:
    def __init__(self, filename):
        self.filename = filename
        self.headlines = self.read_and_clean_csv()

    def read_and_clean_csv(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headlines = [(row[0], float(row[1])) for row in reader]
                return headlines
        except FileNotFoundError:
            return []

    def remove_old_headlines(self):
        current_time = time.time()
        self.headlines = [hd for hd in self.headlines if current_time - hd[1] < 86400]
        self.write_csv()

    def write_csv(self):
        try:
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for row in self.headlines:
                    writer.writerow(row)
        except Exception as e:
            print(f"Error writing to CSV file: {e}")

    def headline_is_similar(self, headline):
        headline = headline.replace('\n', ' ')  # Remove newline characters
        self.remove_old_headlines()
        encoded_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{headline}")
        encoded_headline = np.array(encoded_headline['embedding']).reshape(1,-1)
        for hd in self.headlines:
            compare_headline = ollama.embeddings(model='nomic-embed-text', prompt=f"{hd[0]}")
            compare_headline = np.array(compare_headline['embedding']).reshape(1,-1)
            similarity = cosine_similarity(encoded_headline, compare_headline)
            if similarity > SIMILARITY_THRESHOLD:
                print(headline, "::", hd)
                print("Not posting. Too similar: ", similarity)
                return False
        self.headlines.append((headline, time.time()))
        self.write_csv()
        print(headline, "::", hd)
        print("Similarity: ", similarity)
        print("Posting.")
        return True

    def count_old_headlines(self):
        current_time = time.time()
        with open(self.filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            old_headlines = sum(1 for row in reader if current_time - float(row[1]) > 86400)
        return old_headlines