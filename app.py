from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_comment_downloader import YoutubeCommentDownloader
import feedparser
import urllib.parse
import requests

app = Flask(__name__)

TAVILY_API_KEY = "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"

@app.route('/transcript')
def get_transcript():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Please provide a video id"}), 400
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        return jsonify([{"text": s.text, "start": s.start} for s in transcript])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/comments')
def get_comments():
    video_id = request.args.get('id')
    limit = int(request.args.get('limit', 50))
    if not video_id:
        return jsonify({"error": "Please provide a video id"}), 400
    try:
        downloader = YoutubeCommentDownloader()
        comments = []
        for comment in downloader.get_comments_from_url(f'https://youtube.com/watch?v={video_id}'):
            comments.append(comment)
            if len(comments) >= limit:
                break
        return jsonify(comments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 1. Raw Google News (no content)
@app.route('/news')
def get_news():
    topic = request.args.get('topic', 'artificial intelligence')
    limit = int(request.args.get('limit', 10))
    try:
        query = urllib.parse.quote(topic)
        url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:limit]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": entry.source.title if hasattr(entry, 'source') else "Unknown",
            })
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Google News WITH content (uses Tavily)
@app.route('/news/content')
def get_news_with_content():
    topic = request.args.get('topic', 'artificial intelligence')
    limit = int(request.args.get('limit', 5))
    try:
        query = urllib.parse.quote(topic)
        url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:limit]:
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": entry.source.title if hasattr(entry, 'source') else "Unknown",
                "content": ""
            }
            try:
                r = requests.post(
                    "https://api.tavily.com/extract",
                    json={"urls": [entry.link], "api_key": TAVILY_API_KEY},
                    timeout=10
                )
                data = r.json()
                if data.get("results"):
                    article["content"] = data["results"][0].get("raw_content", "")[:2000]
                    article["actual_url"] = data["results"][0].get("url", entry.link)
            except:
                article["content"] = "Could not fetch content"
            articles.append(article)
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Scrape any single URL
@app.route('/scrape')
def scrape_url():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a url"}), 400
    try:
        r = requests.post(
            "https://api.tavily.com/extract",
            json={"urls": [url], "api_key": TAVILY_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get("results"):
            return jsonify({
                "url": data["results"][0].get("url"),
                "content": data["results"][0].get("raw_content", "")
            })
        return jsonify({"error": "No content found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()