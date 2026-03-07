from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_comment_downloader import YoutubeCommentDownloader
import feedparser
import urllib.parse

app = Flask(__name__)

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

@app.route('/news')
def get_news():
    topic = request.args.get('topic', 'artificial intelligence')
    limit = int(request.args.get('limit', 10))
    include_content = request.args.get('content', 'false').lower() == 'true'
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
            if include_content:
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    headers = {"User-Agent": "Mozilla/5.0"}
                    r = requests.get(entry.link, headers=headers, timeout=5)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraphs = soup.find_all('p')
                    article["content"] = " ".join([p.get_text() for p in paragraphs[:5]])
                except:
                    article["content"] = "Could not fetch content"
            articles.append(article)
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500