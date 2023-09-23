import pandas as pd
import requests
from pathlib import Path

from googleapiclient.discovery import build

from config import API_KEY


def get_youtube_video_data(video_id, api_key):
    """
    Fetches data for a given YouTube video ID using the YouTube Data API v3.

    Parameters:
    - video_id (str): The ID of the YouTube video.
    - api_key (str): Your API key from the Google Developer Console.

    Returns:
    - dict: A dictionary containing the video's data.
    """
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # https://youtu.be/SwSbnmqk3zY?si=l4eo99vsZUzdF_MR&t=2073
    request = youtube.channels().list(
        part="statistics,contentDetails",
        forUsername="schafer5"
    )
    response = request.execute()

    return response

    # base_url = "https://www.googleapis.com/youtube/v3/videos"
    # params = {
    #     "id": video_id,
    #     "key": api_key,
    #     "part": "snippet,statistics"  # You can add more parts as needed
    # }

    # response = requests.get(base_url, params=params)
    # data = response.json()

    # if "items" in data and len(data["items"]) > 0:
    #     return data["items"][0]
    # else:
    #     return None


def main():

    # load the data
    df = pd.read_csv(Path(__file__).parent / "data" / "video_metadata.csv")

    # # Example usage:
    video_id = "qPKd99Pa2iU&t"
    video_data = get_youtube_video_data(video_id, API_KEY)
    print(video_data)


if __name__ == '__main__':
    raise SystemExit(main())
