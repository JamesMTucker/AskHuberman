# Description: Scraper for Huberman Lab Podcast
import os
import time
import logging
import uuid
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import bs4
import pandas as pd
import requests
import selenium.common.exceptions
from tqdm.auto import tqdm
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@dataclass
class Huberman:
    base_url: str = "https://www.hubermanlab.com"
    url: str = f"{base_url}/all-episodes"
    episodes: list = field(default_factory=list)
    thumbnails: list = field(default_factory=list)
    episode_data: list[dict] = field(default_factory=list)
    driver: webdriver.Chrome = field(default_factory=webdriver.Chrome)

    def __post_init__(self):
        """Initialize the class."""
        self.episodes = self.get_episode_meta_data()
        self.episode_data = [self.get_episode_data(url) for url in tqdm(self.episodes, desc="Scraping Episodes")]
        self.records = self._build_dataframe(self.episodes, self.episode_data)

    @staticmethod
    def _chrome_options(*, headless: bool = False, user_agent: str = None):
        """Define the chrome options."""
        co = Options()
        ua = UserAgent()
        
        user_agent = ua.chrome if user_agent is None else user_agent
        co.add_experimental_option("excludeSwitches", ["enable-automation"])
        co.add_experimental_option("useAutomationExtension", False)
        co.add_argument(f"user-agent={user_agent}")
        if headless:
            co.add_argument("--headless=new")
        return co

    @staticmethod
    def _fetch_episode_urls(soup: BeautifulSoup) -> list:
        """Fetch the urls for each episode."""
        # all the episodes are in a div with the class name 'article-wrapper col'
        episodes_wrapper = soup.find_all("div", {"class": "article-wrapper col"})
        
        # inside the article-wrapper col, there is an 'article class' which contains the url
        episodes = [episode.find("article") for episode in episodes_wrapper]
        return [episode.find("a")["href"] for episode in episodes]

    def get_episode_meta_data(self) -> list[str]:
        """The webpage doesn't load all the episodes at once, so we need to scroll down to load more episodes."""
        # use selenium to scroll down the page
        self.driver.get(self.url)
        
        time.sleep(2)

        # get the html
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        page_exists = True
        page_number = 1
        # while the page exists, scroll down, scrape the data, and click on the next page
        while page_exists:
            # scroll down to the bottom of the page
            while True:
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            next_button_element = '/html/body/main/section[2]/div/div[2]/div[3]/div[3]/div/ul/li[8]/a'
            next_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, next_button_element)))

            # scrape the data on the current page
            try:
                next_button.click()
                # get the html source for current page
                html = self.driver.page_source

                print(f'Processing page {page_number}')
                soup = BeautifulSoup(html, "html.parser")

                self.get_episode_data(soup)

                page_number += 1
                time.sleep(2)
            except selenium.common.exceptions.TimeoutException:
                print(f'Processed a total of {page_number} pages')
                page_exists = False

        

        # next_element = self.driver.find_element_by_xpath('//*[@id="pagination"]/div/ul/li[8]/a')
        # next_element.click()
        
        exit()
                
                
                
                
        urls = self._fetch_episode_urls(soup)
        logger.info(f"Found {len(urls)} episodes")
        self.driver.close()
        
        return urls

    def get_episode_data(self, page_source: bs4.BeautifulSoup) -> dict:
        """
        Scrape the metadata for each episode.
        :param page_source: The page source for the episode in an soup object.

        :return: A dictionary of the episode metadata.
        """

        episodes_meta_data = {}

        try:
            # we want the ai-Hits div class
            ai_hits = page_source.find("div", {"id": "hits"})
        except AttributeError:
            logger.info("No episodes found")

        # we want the ol class 'topics-section
        topics_section = ai_hits.find("ol", {"class": "topics-section"})

        # find only the children li items of the topics section
        li_children = topics_section.findChildren("li", recursive=False)

        for li in li_children:
            # get the month from the h2 class
            date_published = li.find("h2")
            month, year = date_published.text.split()

            # episode for the date_published are listed in an li class="ais-Hits-item"
            episodes = li.find_all("li", {"class": "ais-Hits-item"})

            for episode in episodes:
                # extract the episode link
                episode_link = episode.find("a")['href']

                # extract the img thumbnail and description from img alt
                thumbnail = episode.find("img")['src']
                description = episode.find("img")['alt']

                # extract the episode category, date, and primary topic
                category = episode.find("div", {"class": "hit"})['algolia-category']
                date = episode.find("div", {"class": "hit"})['algolia-date']
                primary_topic = episode.find("div", {"class": "hit"})['algolia-primarytopic']


                print(category, date, primary_topic, episode_link, thumbnail, description)

            #     # grab the image thumbnail
            #     thumbnail = episode.find("img")['src']
            #     self.thumbnails.append(thumbnail)
            #
            #     # get the topics list from the div class="topics-list"
            #     topics = episode.find("div", {"class": "topics-list"}).text
            #
            #     # the episode meta data is in a div class="hit-content"
            #     hit_content = episode.find("div", {"class": "hit-content"})
            #
            #     # get the type of episode in the hit-category div
            #     hit_category = hit_content.find("div", {"class": "hit-category"})
            #
            #     # get the episode description from the div class="description"
            #     description = hit_content.find("div", {"class": "description"})
            #
            #     # episode links are in the href of the hit_content
            #     episode_link = hit_content.find("a")['href']
            #     print(f'{self.base_url}{episode_link}')

        # print(episodes)


    # def get_episode_data(self, url: str) -> dict:
    #     """
    #     Each episode is on a separate page, so we need to scrap the data from each page.
    #
    #     title = h1 class="entry-title"
    #     entry_content = div class "entry-content" in the <p> tags
    #     resources = any linked resources
    #     timestamps = h2 class=wp-block-heading id="h-timestamps
    #
    #     """
    #     article = {}
    #
    #     # use requests to get the html
    #     page = requests.get(url)
    #     soup = BeautifulSoup(page.content, "lxml")
    #
    #     # get the title
    #     try:
    #         article['title'] = soup.find("h1", {"class": "entry-title"}).text
    #     except AttributeError:
    #         article['title'] = None
    #
    #     # get the entry content
    #     try:
    #         # the first p contains the links to social media. Skip this p
    #         paragraphs = soup.find("div", {"class": "entry-content"}).find_all("p")[1:]
    #         article['entry_content'] = [paragraph.text.strip() for paragraph in paragraphs]
    #     except AttributeError:
    #         article['entry_content'] = None
    #
    #     # get the resource links: wp-block-heading id="h-resources"
    #     try:
    #         resources = soup.find("h2", {"id": "h-resources"}).find_next("ul").find_all("a")
    #         article['resources'] = [resource['href'] for resource in resources]
    #     except AttributeError:
    #         article['resources'] = None
    #
    #     # get the timestamps: wp-block-heading id="h-timestamps"
    #     try:
    #         timestamps = soup.find("h2", {"id": "h-timestamps"}).find_next("ul").find_all("li")
    #         # get the timestamp links from the li
    #         article['timestamps'] = [timestamp.find("a")['href'] for timestamp in timestamps]
    #         # get the timestamp descriptions from the li text
    #         article['timestamp_descriptions'] = [timestamp.text.strip() for timestamp in timestamps]
    #     except AttributeError:
    #         article['timestamps'] = None
    #         article['timestamp_descriptions'] = None
    #
    #     return article

    def _build_dataframe(self, episodes: list, episode_data: list[dict]) -> pd.DataFrame:
        """Construct the dataframe of the episode data"""
        
        ids = [uuid.uuid4() for _ in range(len(self.episodes))]
        
        episode_data = zip(ids, episodes, episode_data)
        
        df = pd.DataFrame(columns=['video_id', 'video_title',
                                   'video_description', 'video_url',
                                   'video_resources', 'timestamps',
                                   'timestamp_descriptions']
                          )
        
        # add the data to the dataframe
        for idx, episode, meta_data in episode_data:
            df.loc[len(df)] = [idx, meta_data['title'],
                                 meta_data['entry_content'], episode,
                                 meta_data['resources'], meta_data['timestamps'],
                                 meta_data['timestamp_descriptions']
                                ]
        
        return df


def _save_csv(df: pd.DataFrame, path: str):
    """Save the dataframe to a csv file."""
    logger.info(f"Saving data to {path}")
    
    # change the video description to semi-colon separated string
    df.records['video_description'] = df.records['video_description'].apply(lambda x: ' '.join(x) if x is not None else None)
    
    # change video resources to semi-colon separated string
    df.records['video_resources'] = df.records['video_resources'].apply(lambda x: '; '.join(x) if x is not None else None)
    
    # change timestamps to semi-colon separated string
    df.records['timestamps'] = df.records['timestamps'].apply(lambda x: '; '.join(x) if x is not None else None)
    
    # change timestamp descriptions to semi-colon separated string
    df.records['timestamp_descriptions'] = df.records['timestamp_descriptions'].apply(lambda x: '; '.join(x) if x is not None else None)
    
    # clean up for csv
    df.records.to_csv(f'{path}/video_metadata.csv', sep=',', quotechar='"', index=False)


def main():
    """Main function to control the Huberman Lab website to scrap the data for each episode.

    Raises:
        SystemExit: If the script fails to run.
    """
    output_data = Path(__file__).parent / 'data'
    huberman = Huberman()
    
    # make data dir
    if not os.path.exists(output_data):
        logger.info('Creating data directory')
        Path.mkdir(output_data)

    # save the data
    _save_csv(huberman, output_data)
    
    
if __name__ == "__main__":
    raise SystemExit(main())
