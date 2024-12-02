import requests
from bs4 import BeautifulSoup
import json

def get_article_json(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # If the GET request is successful, the status code will be 200
        if response.status_code == 200:
            # Get the content of the response
            page_content = response.content
            
            # Create a BeautifulSoup object and specify the parser
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Remove all script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get the text of the article
            article_text = soup.get_text()
            
            # Break the text into lines and remove leading and trailing space on each
            lines = (line.strip() for line in article_text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            article_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Return the result as JSON
            return json.dumps({"url": url, "article_text": article_text, "paywall": False})
        else:
            return json.dumps({"url": url, "error": "Failed to retrieve the article.", "paywall": False})
    
    except Exception as e:
        return json.dumps({"url": url, "error": str(e), "paywall": False})


def check_paywall(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # If the GET request is successful, the status code will be 200
        if response.status_code == 200:
            # Get the content of the response
            page_content = response.content
            
            # Create a BeautifulSoup object and specify the parser
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Check if the page contains a paywall
            if soup.find("meta", attrs={"name": "paywall"}) or soup.find("div", attrs={"class": "paywall"}):
                return json.dumps({"url": url, "paywall": True, "error": None})
            else:
                return json.dumps({"url": url, "paywall": False, "error": None})
        else:
            return json.dumps({"url": url, "paywall": False, "error": "Failed to check for paywall."})
    
    except Exception as e:
        return json.dumps({"url": url, "paywall": False, "error": str(e)})

def extract_article_text(json_response):
    """
    Extracts the article text from the JSON response.
    
    Args:
        json_response (str): The JSON response containing the article text.
    
    Returns:
        str: The extracted article text.
    """
    try:
        # Load the JSON response into a Python dictionary
        response_dict = json.loads(json_response)
        
        # Extract and return the article text
        return response_dict["article_text"]
    
    except (json.JSONDecodeError, KeyError) as e:
        # Handle JSON decoding or key errors
        print(f"Error extracting article text: {str(e)}")
        return None

def get_article_text_from_json(url): #rewrote the main function to implement all the features above in a single function

    paywall_result = check_paywall(url)
    paywall_json = json.loads(paywall_result)
    
    if paywall_json["paywall"]:
        print(json.dumps({"url": url, "error": "This article is behind a paywall."}, indent=4))
    else:
        article_json_response = get_article_json(url)
        article_text = extract_article_text(article_json_response)
    
    return article_text


