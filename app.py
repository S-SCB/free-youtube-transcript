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
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    # Follow redirects to get actual article URL
                    r = requests.get(entry.link, headers=headers, timeout=8, allow_redirects=True)
                    actual_url = r.url
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # Remove scripts and styles
                    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                        tag.decompose()
                    paragraphs = soup.find_all('p')
                    content = " ".join([p.get_text().strip() for p in paragraphs[:8] if len(p.get_text().strip()) > 50])
                    article["content"] = content if content else "Content blocked by publisher"
                    article["actual_url"] = actual_url
                except Exception as ex:
                    article["content"] = f"Could not fetch: {str(ex)}"
            articles.append(article)
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500