from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_comment_downloader import YoutubeCommentDownloader
from youtube_transcript_api.proxies import GenericProxyConfig

app = Flask(__name__)

PROXY_URL = "http://pc3a9JA3tG-res-any:PC_2NoKG65deJmddoZHE@proxy-us.proxy-cheap.com:59593"

@app.route('/')
def home():
    return jsonify({"status": "ok", "endpoints": ["/transcript?id=VIDEO_ID", "/comments?id=VIDEO_ID&limit=50"]})

@app.route('/transcript')
def get_transcript():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Please provide a video id"}), 400
    try:
        ytt = YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=PROXY_URL,
                https_url=PROXY_URL,
            )
        )
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

if __name__ == '__main__':
    app.run()