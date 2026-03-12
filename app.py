from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_comment_downloader import YoutubeCommentDownloader
from youtube_transcript_api.proxies import GenericProxyConfig
import signal

app = Flask(__name__)

PROXY_URL = "http://pc3a9JA3tG-res-any:PC_2NoKG65deJmddoZHE@proxy-us.proxy-cheap.com:5959"


def timeout_handler(signum, frame):
    raise TimeoutError("Timed out")


@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "endpoints": [
            "/transcript?id=VIDEO_ID",
            "/comments?id=VIDEO_ID&limit=100"
        ]
    })


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
        transcript_list = ytt.list(video_id)
        transcript = transcript_list.find_transcript(
            ['en', 'en-US', 'en-GB', 'en-AU']
        ).fetch()
        return jsonify([{"text": s.text, "start": s.start} for s in transcript])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/comments')
def get_comments():
    video_id = request.args.get('id')
    limit = min(int(request.args.get('limit', 100)), 1000)

    if not video_id:
        return jsonify({"error": "Please provide a video id"}), 400

    comments = []

    try:
        # Fresh downloader every request — avoids corrupted state after timeouts
        downloader = YoutubeCommentDownloader()

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(55)  # 55s — just under Render's 60s hard limit

        for comment in downloader.get_comments_from_url(
            f'https://youtube.com/watch?v={video_id}'
        ):
            comments.append(comment)
            if len(comments) >= limit:
                break

        signal.alarm(0)  # cancel alarm on success
        return jsonify(comments)

    except TimeoutError:
        signal.alarm(0)
        # Return whatever was collected before timeout — not an error
        return jsonify(comments)

    except BaseException as e:
        # Catch absolutely everything else including generator errors
        signal.alarm(0)
        if comments:
            return jsonify(comments)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run()