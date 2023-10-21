import os
import bs4
import json
import jieba
import requests
import datetime
import feedparser
from thefuzz import fuzz
from datetime import timezone

bing_endpoint = 'https://api.bing.microsoft.com/v7.0/search'
top_n = 3

def search_bing(query: str, mkt: str = 'zh-CN'):
    params = {'q': query, 'mkt': mkt}
    headers = {'Ocp-Apim-Subscription-Key': os.environ['BING_API_KEY']}
    # Call the API
    try:
        response = requests.get(bing_endpoint, headers=headers, params=params)
        response.raise_for_status()
        out = []
        for hit in response.json()['webPages']['value'][:top_n]:
            out.append({
                'description': hit['snippet'],
                'url': hit['url']
            })
        return json.dumps(out).encode('utf-8').decode('unicode_escape')
    except Exception as ex:
        raise ex
    
def search_podcasts(query: str):
    d = feedparser.parse('https://www.ximalaya.com/album/58531642.xml')
    data = []
    for entry in d.entries:
        # Use beautifulsoup to process the text
        soup = bs4.BeautifulSoup(entry.summary, 'html.parser')
        # Find all the <p> tags and add them to a list
        paragraphs = [p.text for p in soup.find_all('p')]
        try:
            # Remove all empty string elements in the list as well
            paragraphs = list(filter(None, paragraphs))
            # Cut everything after "说在最后" (including it)
            paragraphs = paragraphs[:paragraphs.index('说在最后')]
        except ValueError:
            pass
        text = '\n'.join(paragraphs)
        # Calculate the similarity between the query and the entry
        title_score = fuzz.token_set_ratio(" ".join(jieba.cut(query)), " ".join(jieba.cut(entry.title)))
        text_score = fuzz.token_set_ratio(" ".join(jieba.cut(query)), " ".join(jieba.cut(text)))
        data.append({
            'title': entry.title,
            'link': entry.link,
            'text': text,
            'score': title_score * text_score
        })
    # Sort the results by similarity
    data = sorted(data, key=lambda x: x['score'], reverse=True)
    # Return the top 3 results
    return json.dumps(data[:3]).encode('utf-8').decode('unicode_escape')
    
def get_functions_prompt():
    dt = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return [
        {
            'name': 'search_bing',
            'description': f'Search Bing for web results on factual or topical questions. It is {dt} UTC now.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query based on user message.'
                    }
                },
                'required': ['query']
            }
        },
        {
            'name': 'search_podcasts',
            'description': 'Search through《扩博智聊》podcast archives for relevant episodes.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query based on user message.'
                    }
                },
                'required': ['query']
            }
        }
    ]

available_functions = {
    "search_bing": search_bing,
    "search_podcasts": search_podcasts
}
    
if __name__ == '__main__':
    # print(search_podcasts("自动驾驶"))
    # print(search_bing('扩博智聊'))
    pass