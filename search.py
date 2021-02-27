import requests
import logging
import json
import os
import shutil
from bs4 import BeautifulSoup
from dataclasses import dataclass
from configuration import (
    WIKIPEDIA_HOST_URL,
    WIKIPEDIA_SEARCH_API
)

LOGGER_BASENAME = 'wikisearch'
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())

@dataclass
class SearchResult:
    title: str
    url: str

class LoggerMixin(object):
    def __init__(self) -> None:
        self._logger = logging.getLogger(f'{LOGGER_BASENAME}.{self.__class__.__name__}')

class WikipediaSeries(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.search_url = WIKIPEDIA_SEARCH_API
        self.seasons = []
        self.title = None

    def __str__(self):
        return f'series seasons: {self.seasons}'
    
    def _get_query_map(self, name):
        query_map = {
            'episode_list': f'list of {name} episodes',
            'miniseries': f'{name} miniseries',
            'name': f'{name}'
        }
        return query_map

    def search_by_name(self, name):
        for type, query in self._get_query_map(name).items():
            self._logger.debug(f'Searching for {name} with type:{type}')
            result = self._search(query)
            if result:
                if len(result) == 1:
                    self.title = name
                return result
    
    def _search(self, query):
        parameters = {'action': 'opensearch',
                            'format': 'json',
                            'formatversion': '2',
                            'search': query}

        response = requests.get(self.search_url, params=parameters)
        if response.ok:
            return [SearchResult(*args) for args in zip(response.json()[1], response.json()[3])]
        else:
            self._logger.error(f'Request failed with code {response.code} and message {response.text}')
        
    
    def get_soup_by_url(self, url):
        html_response = requests.get(url)
        soup = BeautifulSoup(html_response.text, 'html.parser')
        return soup
    
    def parse_seasons_from_soup(self, soup):
        season_list = []
        table = soup.find("table", {"class": "wikitable plainrowheaders"})
        t_headers = table.find_all("th")
        for header in t_headers:
            season = header.find("a")
            if season:
                season_list.append(season.contents[0])
        return season_list

    def parse_seasons_and_episodes_from_soup(self, soup):
        season_list = []
        tables = soup.find_all("table", {"class": "wikitable plainrowheaders wikiepisodetable"})
        for table in tables:
            episode_list = []
            season_header = table.find_previous_sibling('h3')
            season_title = season_header.find("span", {"class": "mw-headline"}).get_text(strip=True)
            season = Season(season_title)
            season.episodes = self.parse_html_table_to_json(table)
            season_list.append(season)
        self.seasons = season_list
    
    def parse_html_table_to_json(self, table):
        table_data = [[cell.text.strip('"') for cell in row] for row in table("tr", {"class": "vevent"})]
        table_headers = [cell.text.strip() for cell in table.find("tr")("th", {"scope": "col"})]
        results_list = []
        for row in table_data:
            res_dict = {}
            for idx, item in enumerate(row):
                res_dict[table_headers[idx]] = item
            results_list.append(res_dict)
        return json.dumps(results_list, indent=4)

    def write_to_file_system(self):
        for season in self.seasons:
            self._logger.debug(f"writing results to file sysytem for season: {season.number}")
            directory = os.path.dirname(f'./results/{self.title}/{season.number}/')
            if os.path.exists(directory):
                self._logger.warning(f"Season folder already exists {directory}, overwriting it.")
                self.delete_dir_tree(directory)
            os.makedirs(directory)
            with open(f'{directory}/episodes.json', 'w') as episodes_file: 
                episodes_file.write(season.episodes)
    
    def delete_dir_tree(self, dir_path):
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            self._logger.error(f"Error: {dir_path} : {e.strerror}")

class Season:
    
    def __init__(self, number) -> None:
        super().__init__()
        self.number = number
        self.episodes = []
    
    def get_episodes_json(self):
        episodes = []
        for episode in self.episodes:
            episodes.append(episode.__dict__)
        return json.dumps(episodes)


class Episode:

    def __init__(self, title, number) -> None:
        super().__init__()
        self.title = title
        self.number = number

    def __str__(self):
        return f'episode:{self.number},  title:{self.title}'

