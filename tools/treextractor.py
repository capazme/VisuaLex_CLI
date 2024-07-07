import requests
from bs4 import BeautifulSoup
from functools import lru_cache
from .config import MAX_CACHE_SIZE
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_tree(normurn, link=False):
    # Sending HTTP GET request to the provided URL
    response = requests.get(normurn)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the div with id 'albero'
        tree = soup.find('div', id='albero')
        
        # Check if the div exists
        if tree:
            # Find all ul elements within the div
            uls = tree.find_all('ul')
            if uls:
                result = []
                count = 0
                # Process each ul found
                for ul in uls:
                    # Extract all 'a' elements with class 'numero_articolo' within this ul
                    list_items = ul.find_all('a', class_='numero_articolo')
                    
                    for a in list_items:
                        # Check if the parent li element has classes that start with "agg" or contain "collapse"
                        parent_li = a.find_parent('li')
                        if parent_li:
                            classes = parent_li.get('class', [])
                            if any(cls.startswith('agg') for cls in classes) or any('collapse' in cls for cls in classes):
                                continue
                        
                        # Extract text and format it properly
                        text_content = a.get_text(separator=" ", strip=True)
                        
                        if "art." in text_content:
                            text_content=text_content[5:]
                            
                        if link:
                            # Construct modified URL
                            # Use regex to find the article part to replace in the normurn
                            article_part = re.search(r'art\d+', normurn)
                            if article_part:
                                modified_url = normurn.replace(article_part.group(), 'art' + text_content.split()[0])
                            else:
                                modified_url = normurn  # fallback in case regex fails
                            
                            # Create dictionary with text content as key and modified URL as value
                            item_dict = {text_content: modified_url}
                            result.append(item_dict)
                            count += 1
                        else:
                            # If link is False, append only text content
                            result.append(text_content)
                    
                return result, count
            else:
                return "No 'ul' element found within the 'albero' div"
        else:
            return "Div with id 'albero' not found"
    else:
        return f"Failed to retrieve the page, status code: {response.status_code}"

