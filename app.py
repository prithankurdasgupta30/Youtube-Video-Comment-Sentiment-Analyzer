from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from googleapiclient.discovery import build
from dotenv import load_dotenv
from textblob import TextBlob
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

youtube = build("youtube", "v3", developerKey=API_KEY)

app = FastAPI(title="YouTube Sentiment Analysis API")


class VideoRequest(BaseModel):
    video_id: str
    max_comments: int = 20


def analyze_sentiment(text: str):
    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return Path("index.html").read_text()


@app.post("/analyze_video/")
def analyze_video(data: VideoRequest):

    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=data.video_id,
            maxResults=min(data.max_comments, 100),
            textFormat="plainText"
        )

        response = request.execute()

        results = []
        positive = 0
        negative = 0
        neutral = 0

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            sentiment = analyze_sentiment(comment)

            if sentiment == "Positive":
                positive += 1
            elif sentiment == "Negative":
                negative += 1
            else:
                neutral += 1

            results.append({
                "comment": comment,
                "sentiment": sentiment
            })

        total = len(results)

        return {
            "video_id": data.video_id,
            "total_comments_analyzed": total,
            "summary": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral
            },
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))