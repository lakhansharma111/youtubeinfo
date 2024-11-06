import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = "write api key here "

youtube = build('youtube', 'v3', developerKey=API_KEY)

# Function to get channel ID from a YouTube handle (channel URL)
def get_channel_id_from_handle(handle):
    try:
        request = youtube.channels().list(
            part="id",
            forUsername=handle.replace('@', '')
        )
        response = request.execute()
        if response.get("items"):
            return response["items"][0]["id"]
        else:
            print("Channel not found!")
            return None
    except HttpError as e:
        print(f"An error occurred: {e}")
        return None

# Function to get video details from a channel
def get_video_details(channel_id):
    videos_data = []
    try:
        # Fetch the videos from the channel
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50  # You can change the maxResults as needed
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            video_data = {
                "Video ID": video_id,
                "Title": snippet["title"],
                "Description": snippet["description"],
                "Published date": snippet["publishedAt"],
                "Thumbnail URL": snippet["thumbnails"]["high"]["url"],
            }
            
            # Fetch video statistics like views, likes, and comments count
            stats_request = youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            )
            stats_response = stats_request.execute()
            stats = stats_response.get("items", [])[0]
            video_data.update({
                "View count": stats["statistics"].get("viewCount", 0),
                "Like count": stats["statistics"].get("likeCount", 0),
                "Comment count": stats["statistics"].get("commentCount", 0),
                "Duration": stats["contentDetails"].get("duration", "")
            })
            videos_data.append(video_data)
    except HttpError as e:
        print(f"An error occurred: {e}")
    return videos_data

# Function to get comments for a video
def get_video_comments(video_id):
    comments_data = []
    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100  # Fetch the latest 100 comments
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comment_data = {
                "Video ID": video_id,
                "Comment ID": item["id"],
                "Comment text": comment["textDisplay"],
                "Author name": comment["authorDisplayName"],
                "Published date": comment["publishedAt"],
                "Like count": comment.get("likeCount", 0),
                "Reply to": None  # Initial comment, no replies yet
            }
            comments_data.append(comment_data)

            # Fetch replies if available
            if "replies" in item:
                for reply in item["replies"]["comments"]:
                    reply_data = {
                        "Video ID": video_id,
                        "Comment ID": reply["id"],
                        "Comment text": reply["snippet"]["textDisplay"],
                        "Author name": reply["snippet"]["authorDisplayName"],
                        "Published date": reply["snippet"]["publishedAt"],
                        "Like count": reply["snippet"].get("likeCount", 0),
                        "Reply to": item["id"]
                    }
                    comments_data.append(reply_data)
    except HttpError as e:
        print(f"An error occurred: {e}")
    return comments_data

# function to fetch data and save it to Excel
def fetch_and_save_youtube_data(channel_handle):
    channel_id = get_channel_id_from_handle(channel_handle)
    if not channel_id:
        return
    
    videos = get_video_details(channel_id)
    videos_df = pd.DataFrame(videos)

    comments_data = []
    for video in videos_df["Video ID"]:
        comments = get_video_comments(video)
        comments_data.extend(comments)
    
    comments_df = pd.DataFrame(comments_data)

    with pd.ExcelWriter(f"{channel_handle}_youtube_data.xlsx", engine="openpyxl") as writer:
        videos_df.to_excel(writer, sheet_name="Video Data", index=False)
        comments_df.to_excel(writer, sheet_name="Comments Data", index=False)
    
    print("Data has been saved to Excel successfully!")


channel_handle = " enter youtube chanel data"
fetch_and_save_youtube_data(channel_handle)
