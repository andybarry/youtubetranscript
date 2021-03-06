# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask
from flask import request
from flask import Flask, render_template
from flask import Response

import requests

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import VideoUnavailable
from youtube_transcript_api import TranscriptsDisabled
from youtube_transcript_api import NoTranscriptAvailable
import os

USE_CACHE = False

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}
def html_escape(text):
    return "".join(html_escape_table.get(c,c) for c in text)

#import requests_toolbelt.adapters.appengine

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

def format_line(video_id, line):
    start = line['start']
    duration = line['duration']
    #end = start+duration
    text = line['text']
    out = '<text start="' + str(start) + '" dur="' + str(duration) + '">' + html_escape(text) + '</text>'
    return out

def format_transcript(video_id, trans):
    one_break = 0
    two_break = 5
    
    out = '<?xml version="1.0" encoding="utf-8" ?><transcript>'
    last_t = 0
    for line in trans:
        out += format_line(video_id, line)
    out += '</transcript>'
    return out

def get_transcript(video_id):
    # Check for a cached version of the transcript
    if USE_CACHE:
        cache_dir = "cache"
        for f in os.listdir(cache_dir):
            if f == video_id:
                # Read the file
                with open(cache_dir + "/" + f, 'r') as f2:
                    print('Cache hit')
                    return f2.read()

        print('Cache miss')
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatted = format_transcript(video_id, transcript)
    if USE_CACHE:
        f = open(cache_dir + "/" + video_id, "w")
        f.write(formatted)
        f.close()

        # Limit cache to 1000 files
        cache_limit = 1000
        list_of_files = os.listdir(cache_dir)
        if len(list_of_files) > cache_limit:
            # Delete the oldest file
            full_path = [cache_dir + "/{0}".format(x) for x in list_of_files]
            oldest_file = min(full_path, key=os.path.getctime)
            os.remove(oldest_file)
            print('removing ', oldest_file)
    
    return formatted

@app.route('/')
def hello():
    if request.args.get('server_vid') is None or len(request.args.get('server_vid')) < 1:
        return render_template("index2.html")

    # Otherwise, do server-side caption getting:
    
    # Read the youtube link
    video_id = request.args.get('server_vid')
    # print(video_url)
    # # Parse the url
    # f = None
    # if 'youtu.be/' in video_url:
        # f = video_url.find('youtu.be/') + 9
    # elif 'v=' in video_url:
        # f = video_url.find('v=') + 2

    # if f is None:
        # return render_template("get_caption.html", transcript='Failed to parse URL')

    # video_id = video_url[f:f+11]

    # return render_template("output_page.html", video_id=video_id)

    print('video id = ', video_id)
    try:
        transcript = get_transcript(video_id)
    except VideoUnavailable as e:
        # Render the captcha
        return Response('<?xml version="1.0" encoding="utf-8" ?><error>Error: video unavailable</error>', mimetype='text/xml')
    except TranscriptsDisabled as e:
        return Response('<?xml version="1.0" encoding="utf-8" ?><error>Error: transcripts disabled for that video</error>', mimetype='text/xml')
    except NoTranscriptAvailable as e:
        return Response('<?xml version="1.0" encoding="utf-8" ?><error>Error: No transcript available for that video</error>', mimetype='text/xml')
    except Exception as e:
        return Response('<?xml version="1.0" encoding="utf-8" ?><error>:( Unknown error:' + str(e) + '</error>', mimetype='text/xml')
        # return render_template("starting_page.html", header_text='That failed: ' + str(e))

    #return render_template("output_page.html", video_id=video_id, transcript=transcript)
    return Response(transcript, mimetype='text/xml')
    #return render_template("get_caption.html", transcript=transcript)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
