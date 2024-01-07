# Description: Scraper for Huberman Lab Podcast
import os
import time
import logging
import uuid
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import bs4
from fake_useragent.settings import metadata
import pandas as pd
import requests
from selenium.common.exceptions import TimeoutException
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
    episodes_metadata: list = field(default_factory=list)
    episode_data: list[dict] = field(default_factory=list)
    episodes_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    driver: webdriver.Chrome = field(default_factory=webdriver.Chrome)

    def __post_init__(self):
        """Initialize the class."""
        self._get_episode_meta_data() # populate the episodes_metadata
        # parse the data for each episode
        episode_link = self.episodes_df.episode_link.tolist()
        self.episode_data = [self._parse_episode_data(url) for url in tqdm(episode_link, desc="Scraping Episodes")]
        # merge the self.episode_data onto the self.episodes_df
        self.episodes_df['show_notes'] = self.episode_data
        self.episodes_df.to_csv('huberman.csv', index=True)
        exit()
        self.records = self._build_dataframe(self.episodes_metadata, self.episode_data)

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

    def _get_episode_meta_data(self) -> list:
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
            # progress through the pages to get all the episodes
            next_button_element = '/html/body/main/section[2]/div/div[2]/div[3]/div[3]/div/ul/li[8]/a'
          
            # scroll down to the bottom of the page to populate the page with more episodes
            while True:
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # get the html source for current page
            html = self.driver.page_source
            logger.info(f'Processing page {page_number}')

            # parse the html
            soup = BeautifulSoup(html, "html.parser")
            self._parse_metadata(soup)

            # paginate to the next page
            try:
                next_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, next_button_element)))
                # increase the page number
                page_number += 1
                next_button.click()
                time.sleep(2)
            except TimeoutException:
                logger.info(f'Processed a total of {page_number} pages')
                page_exists = False
                break
    
    def _parse_metadata(self, page_source: bs4.BeautifulSoup) -> dict:
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
                # create an empty dataframe
                df = pd.DataFrame()

                # create an id for the episode
                episode_id = uuid.uuid4()

                # extract the episode link
                episode_link = episode.find("a")['href']

                # extract the img thumbnail and description from img alt
                thumbnail = episode.find("img")['src']
                title = episode.find("img")['alt']
                description = episode.find("div", {"class": "description"}).text

                # extract the episode category, date, and primary topic
                category = episode.find("div", {"class": "hit"})['algolia-category']
                date = episode.find("div", {"class": "hit"})['algolia-date']
                # the primary topic is defined in the attribute
                primary_topic = episode.find("div", {"class": "hit"})['algolia-primarytopic']

                # we also want the other topics in the div class="topics-list"
                topics_listed = episode.find("div", {"class": "topics-list"})
                # extract the list of topics from the a href into a list
                topics = [topic.text for topic in topics_listed.find_all("a")]

                # grab the image thumbnail
                thumbnail = episode.find("img")['src']


                # add the data to the dictionary
                episodes_meta_data[episode_id] = {
                    "episode_link": episode_link,
                    "thumbnail": thumbnail,
                    "title": title,
                    "description": description,
                    "category": category,
                    "date": date,
                    "primary_topic": primary_topic,
                    "topics": topics
                }

                # convert to a dataframe
                df = pd.DataFrame.from_dict(episodes_meta_data, orient='index')
                # append to class dataframe
                self.episodes_df = pd.concat([self.episodes_df, df])

                # append the episode link to the self.episode_meta_data list
                self.episodes_metadata.append(episodes_meta_data)

    def _parse_episode_data(self, episode: dict) -> dict:
        """
        Each episode is on a separate page, so we need to scrap the data from each page.

        title = h1 class="entry-title"
        entry_content = div class "entry-content" in the <p> tags
        resources = any linked resources
        timestamps = h2 class=wp-block-heading id="h-timestamps
        """
        # get the page source with chrome
        logger.info(f"Processing episode {episode}")
        page = requests.get(f"{self.base_url}{episode}")
        print(page.status_code)
        soup = BeautifulSoup(page.content, "lxml")
        
        # get the show notes in div class="rich-text-episode-notes w-richtext" (get content in p and li tags)
        show_notes = soup.find("div", {"class": "rich-text-episode-notes w-richtext"}).find_all(["p", "li"])
        show_notes = " ".join([note.text.strip() for note in show_notes])
        self.episode_data.append(show_notes)

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
