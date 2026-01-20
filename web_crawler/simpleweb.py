import requests
from bs4 import BeautifulSoup
from collections import deque
import networkx as nx
import matplotlib.pyplot as plt

def build_transition_graph(start_url, max_depth=2):
    # Use a set to keep track of visited URLs and a queue for BFS
    visited_urls = set()
    url_queue = deque([(start_url, 0)])
    graph = nx.DiGraph()

    while url_queue:
        current_url, depth = url_queue.popleft()

        if current_url in visited_urls or depth > max_depth:
            continue
        
        print(f"Crawling: {current_url} (Depth: {depth})")
        visited_urls.add(current_url)
        
        try:
            response = requests.get(current_url, timeout=5)
            response.raise_for_status() # Raise an exception for bad status codes
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                next_url = link['href']
                # Basic relative URL handling (requires more robust implementation for production)
                if not next_url.startswith('http'):
                    next_url = requests.compat.urljoin(current_url, next_url)
                
                # Only add internal links to the graph for this example
                if next_url.startswith(start_url.split('://')[0] + '://' + start_url.split('://')[1].split('/')[0]):
                    graph.add_edge(current_url, next_url)
                    if next_url not in visited_urls:
                        url_queue.append((next_url, depth + 1))

        except requests.exceptions.RequestException as e:
            print(f"Error crawling {current_url}: {e}")

    return graph


target_website = "https://seleniumbase.io/" 
website_graph = build_transition_graph(target_website)

# To visualize the graph using networkx and matplotlib
plt.figure(figsize=(10, 10))
pos = nx.spring_layout(website_graph, seed=42) # Positions for all nodes
nx.draw(website_graph, pos, with_labels=True, node_size=50, font_size=8, arrows=True)
plt.show()
