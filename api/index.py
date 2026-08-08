from flask import Flask, jsonify, request, render_template_string, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests
import re
import json

app = Flask(__name__)
CORS(app)

# --- NEXUS CLONE WEB UI ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXUS Clone - Stream Pro</title>
    <style>
        :root {
            --bg-color: #0f0f0f;
            --surface-color: #212121;
            --hover-color: #272727;
            --primary: #3b82f6;
            --text: #f1f1f1;
            --text-muted: #aaaaaa;
            --nexus-blue: #2563eb;
            --border-color: #272727;
        }
        * { box-sizing: border-box; }
        body { 
            font-family: "Roboto", Arial, sans-serif;
            background: var(--bg-color); 
            color: var(--text); 
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }

        .header {
            background: var(--bg-color);
            padding: 0 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            height: 56px;
            z-index: 200;
            flex-shrink: 0;
        }
        .header-left { display: flex; align-items: center; gap: 16px; }
        .menu-btn {
            background: none; border: none; color: var(--text); font-size: 18px; 
            cursor: pointer; padding: 8px; border-radius: 50%;
        }
        .menu-btn:hover { background: var(--hover-color); }
        .logo { 
            font-size: 18px; color: var(--text); font-weight: bold; 
            display: flex; align-items: center; gap: 6px; cursor: pointer; text-decoration: none;
        }
        .logo-badge { background: var(--nexus-blue); color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
        
        .search-container { position: relative; flex: 1; max-width: 600px; margin: 0 20px; }
        .input-group { display: flex; width: 100%; }
        input#queryInput { 
            width: 100%; padding: 0 16px; height: 40px; font-size: 15px; 
            background: #121212; color: var(--text); border: 1px solid #323232; 
            border-radius: 40px 0 0 40px; outline: none;
        }
        input#queryInput:focus { border-color: var(--primary); }
        button.search-btn { 
            width: 64px; height: 40px; background: #222; border: 1px solid #323232; 
            border-left: none; border-radius: 0 40px 40px 0; cursor: pointer; color: var(--text); 
        }
        button.search-btn:hover { background: #333; }

        .suggestions-box {
            position: absolute; top: 45px; left: 0; right: 0; background: var(--surface-color);
            border-radius: 12px; border: 1px solid #333; display: none; flex-direction: column;
            overflow: hidden; z-index: 300; box-shadow: 0 10px 25px rgba(0,0,0,0.8);
        }
        .suggestion-item { padding: 10px 16px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 10px; }
        .suggestion-item:hover { background: var(--hover-color); }

        .app-body { display: flex; flex: 1; overflow: hidden; position: relative; }

        .sidebar {
            width: 240px; background: var(--bg-color); padding: 12px; display: flex;
            flex-direction: column; gap: 4px; border-right: 1px solid var(--border-color);
            transition: transform 0.3s ease; flex-shrink: 0;
        }
        .sidebar.collapsed { display: none; }
        .nav-item {
            display: flex; align-items: center; gap: 24px; padding: 10px 12px;
            border-radius: 10px; cursor: pointer; color: var(--text); font-size: 14px; font-weight: 500;
        }
        .nav-item:hover { background: var(--hover-color); }
        .nav-item.active { background: var(--surface-color); font-weight: bold; }

        .content-area { flex: 1; overflow-y: auto; padding: 20px; position: relative; }
        .chips-bar { display: flex; gap: 12px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; }
        .chip { background: var(--surface-color); padding: 6px 12px; border-radius: 8px; font-size: 14px; cursor: pointer; white-space: nowrap; }
        .chip.active { background: #fff; color: #000; font-weight: bold; }

        .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
        .video-card { display: flex; flex-direction: column; cursor: pointer; border-radius: 12px; overflow: hidden; }
        .video-card:hover .thumb-wrap img { transform: scale(1.03); }
        
        .thumb-wrap { width: 100%; aspect-ratio: 16/9; background: #202020; border-radius: 12px; overflow: hidden; position: relative; }
        .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.2s ease; }
        
        .card-details { display: flex; gap: 12px; padding: 10px 2px; }
        .channel-avatar { width: 36px; height: 36px; border-radius: 50%; background: #333; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .card-info { display: flex; flex-direction: column; }
        .card-title { font-size: 15px; font-weight: 500; line-height: 1.3; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .card-uploader { font-size: 13px; color: var(--text-muted); }

        .watch-container { display: none; gap: 24px; width: 100%; max-width: 1600px; margin: 0 auto; }
        .primary-column { flex: 2.5; display: flex; flex-direction: column; }
        .secondary-column { flex: 1; display: flex; flex-direction: column; gap: 12px; }

        .main-player-box { width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        video#mainVideo { width: 100%; height: 100%; }

        .watch-details { margin-top: 15px; }
        .watch-title { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
        .watch-actions { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 15px; }
        .action-btn { background: var(--surface-color); border: none; color: var(--text); padding: 8px 16px; border-radius: 20px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px; }
        .action-btn:hover { background: var(--hover-color); }

        .miniplayer {
            position: fixed; bottom: 20px; right: 20px; width: 320px; height: 180px;
            background: #000; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.9);
            z-index: 500; display: none; flex-direction: column; border: 1px solid #333; overflow: hidden;
        }
        .miniplayer-controls {
            position: absolute; top: 0; left: 0; right: 0; background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
            padding: 8px; display: flex; justify-content: space-between; opacity: 0; transition: opacity 0.2s;
        }
        .miniplayer:hover .miniplayer-controls { opacity: 1; }
        .mini-btn { background: none; border: none; color: white; cursor: pointer; font-size: 16px; }

        .modal-overlay {
            display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8);
            z-index: 1000; justify-content: center; align-items: center;
        }
        .modal-card {
            background: var(--surface-color); padding: 24px; border-radius: 16px;
            width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto; border: 1px solid #333;
        }
        .key-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a2a; font-size: 14px; }
        .key-badge { background: #333; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-weight: bold; color: var(--primary); }

        .loader-box { display: none; position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); flex-direction: column; align-items: center; gap: 12px; z-index: 1000; }
        .spinner { width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.1); border-left-color: var(--nexus-blue); border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <div class="header">
        <div class="header-left">
            <button class="menu-btn" onclick="toggleSidebar()">☰</button>
            <a class="logo" onclick="loadFeed('Trending')">
                ▶ NEXUS <span class="logo-badge">Clone</span>
            </a>
        </div>

        <div class="search-container">
            <div class="input-group">
                <input type="text" id="queryInput" placeholder="Search" value="trending songs" oninput="handleSuggestions(this.value)">
                <button class="search-btn" onclick="executeSearch()">🔍</button>
            </div>
            <div id="suggestionsBox" class="suggestions-box"></div>
        </div>

        <div>
            <button class="action-btn" onclick="toggleKeybindingsModal()">⌨ Shortcuts (?)</button>
        </div>
    </div>

    <div class="app-body">
        <div class="sidebar" id="sidebar">
            <div class="nav-item active" onclick="loadFeed('Home')">🏠 Home</div>
            <div class="nav-item" onclick="loadFeed('Trending')">🔥 Trending</div>
            <div class="nav-item" onclick="loadFeed('Music')">🎵 Music</div>
            <div class="nav-item" onclick="loadFeed('Gaming')">🎮 Gaming</div>
            <hr style="border:0; border-top:1px solid var(--border-color); margin: 10px 0;">
            <div style="padding: 0 12px; font-size: 12px; color: var(--text-muted);">Library</div>
            <div class="nav-item" onclick="alert('Feature coming soon')">📜 History</div>
            <div class="nav-item" onclick="alert('Feature coming soon')">⭐ Liked Videos</div>
        </div>

        <div class="content-area" id="contentArea">
            <div class="chips-bar" id="chipsBar">
                <div class="chip active" onclick="loadFeed('All')">All</div>
                <div class="chip" onclick="loadFeed('Acoustic Pop')">Music</div>
                <div class="chip" onclick="loadFeed('Live Performances')">Live</div>
                <div class="chip" onclick="loadFeed('Podcast')">Podcasts</div>
                <div class="chip" onclick="loadFeed('Lo-Fi Hip Hop')">Lo-Fi</div>
            </div>

            <div class="video-grid" id="videoGrid"></div>

            <div class="watch-container" id="watchContainer">
                <div class="primary-column">
                    <div class="main-player-box" id="playerParent">
                        <video id="mainVideo" controls autoplay playsinline></video>
                    </div>
                    <div class="watch-details">
                        <div class="watch-title" id="videoTitle">Select a video</div>
                        <div class="watch-actions">
                            <span id="videoUploader" style="color:var(--text-muted);">Channel Name</span>
                            <div style="display:flex; gap:10px;">
                                <button class="action-btn" onclick="minimizeToMiniplayer()">🗗 Miniplayer (i)</button>
                                <button class="action-btn" onclick="alert('Link Copied!')">🔗 Share</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="secondary-column" id="upNextList"></div>
            </div>
        </div>
    </div>

    <div class="miniplayer" id="miniplayer">
        <div class="miniplayer-controls">
            <button class="mini-btn" onclick="maximizeFromMiniplayer()">⛶</button>
            <button class="mini-btn" onclick="closeMiniplayer()">✕</button>
        </div>
    </div>

    <div class="modal-overlay" id="keyModal" onclick="if(event.target===this) toggleKeybindingsModal()">
        <div class="modal-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 style="margin:0;">Keyboard Shortcuts</h3>
                <button class="mini-btn" onclick="toggleKeybindingsModal()">✕</button>
            </div>
            <div class="key-row"><span>Play / Pause</span><span class="key-badge">Space</span> or <span class="key-badge">K</span></div>
            <div class="key-row"><span>Seek Backward 5s</span><span class="key-badge">←</span> or <span class="key-badge">J</span></div>
            <div class="key-row"><span>Seek Forward 5s</span><span class="key-badge">→</span> or <span class="key-badge">L</span></div>
            <div class="key-row"><span>Volume Up 10%</span><span class="key-badge">↑</span></div>
            <div class="key-row"><span>Volume Down 10%</span><span class="key-badge">↓</span></div>
            <div class="key-row"><span>Mute / Unmute</span><span class="key-badge">M</span></div>
            <div class="key-row"><span>Toggle Fullscreen</span><span class="key-badge">F</span></div>
            <div class="key-row"><span>Toggle Miniplayer</span><span class="key-badge">I</span></div>
            <div class="key-row"><span>Jump to Percentage</span><span class="key-badge">0 - 9</span></div>
            <div class="key-row"><span>Frame Seek</span><span class="key-badge">,</span> / <span class="key-badge">.</span></div>
            <div class="key-row"><span>Next Video</span><span class="key-badge">Shift + N</span></div>
            <div class="key-row"><span>Shortcuts Menu</span><span class="key-badge">?</span></div>
        </div>
    </div>

    <div class="loader-box" id="loader">
        <div class="spinner"></div>
        <span style="font-size:14px;" id="loaderText">Loading Content...</span>
    </div>

    <script>
        let currentQueue = [];
        let activeVideo = null;
        let isMiniplayerActive = false;

        window.onload = () => {
            loadFeed('Trending');
            setupKeyboardShortcuts();
        };

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('collapsed');
        }

        function toggleKeybindingsModal() {
            const modal = document.getElementById('keyModal');
            modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
        }

        function loadFeed(topic) {
            closeWatchView();
            showLoader(`Fetching ${topic}...`);
            fetch(`/api/search?q=${encodeURIComponent(topic)}`)
                .then(r => r.json())
                .then(data => {
                    hideLoader();
                    if(data.results) {
                        currentQueue = data.results;
                        renderGrid(data.results);
                    }
                });
        }

        function executeSearch() {
            const q = document.getElementById('queryInput').value.trim();
            if(!q) return;
            document.getElementById('suggestionsBox').style.display = 'none';
            loadFeed(q);
        }

        function renderGrid(videos) {
            const grid = document.getElementById('videoGrid');
            grid.innerHTML = "";
            videos.forEach(v => {
                const card = document.createElement('div');
                card.className = 'video-card';
                card.onclick = () => playVideo(v.id);
                card.innerHTML = `
                    <div class="thumb-wrap">
                        <img src="${v.thumbnail}" alt="thumb">
                    </div>
                    <div class="card-details">
                        <div class="channel-avatar">${v.uploader.charAt(0)}</div>
                        <div class="card-info">
                            <div class="card-title">${v.title}</div>
                            <div class="card-uploader">${v.uploader}</div>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function playVideo(id) {
            const v = currentQueue.find(item => item.id === id);
            activeVideo = v;

            document.getElementById('chipsBar').style.display = 'none';
            document.getElementById('videoGrid').style.display = 'none';
            document.getElementById('watchContainer').style.display = 'flex';

            if(isMiniplayerActive) maximizeFromMiniplayer();

            showLoader("Starting stream proxy...");

            const videoNode = document.getElementById('mainVideo');
            videoNode.pause();
            videoNode.src = `/api/stream-video?q=${encodeURIComponent(id)}`;

            videoNode.oncanplay = () => {
                hideLoader();
            };

            videoNode.play().catch(e => console.log("Autoplay blocked:", e));

            if(v) {
                document.getElementById('videoTitle').innerText = v.title;
                document.getElementById('videoUploader').innerText = `Channel: ${v.uploader}`;
            }

            renderUpNext(id);
        }

        function renderUpNext(currentId) {
            const container = document.getElementById('upNextList');
            container.innerHTML = "<h3>Up Next</h3>";
            currentQueue.filter(v => v.id !== currentId).forEach(v => {
                const item = document.createElement('div');
                item.style.cssText = "display:flex; gap:10px; cursor:pointer;";
                item.onclick = () => playVideo(v.id);
                item.innerHTML = `
                    <img src="${v.thumbnail}" style="width:120px; aspect-ratio:16/9; border-radius:8px; object-fit:cover;">
                    <div>
                        <div style="font-size:13px; font-weight:bold; line-height:1.2;">${v.title}</div>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${v.uploader}</div>
                    </div>
                `;
                container.appendChild(item);
            });
        }

        function closeWatchView() {
            document.getElementById('watchContainer').style.display = 'none';
            document.getElementById('chipsBar').style.display = 'flex';
            document.getElementById('videoGrid').style.display = 'grid';
        }

        function minimizeToMiniplayer() {
            const videoNode = document.getElementById('mainVideo');
            const mini = document.getElementById('miniplayer');

            mini.appendChild(videoNode);
            mini.style.display = 'flex';
            isMiniplayerActive = true;
            closeWatchView();
        }

        function maximizeFromMiniplayer() {
            const playerBox = document.getElementById('playerParent');
            const videoNode = document.getElementById('mainVideo');
            const mini = document.getElementById('miniplayer');

            playerBox.appendChild(videoNode);
            mini.style.display = 'none';
            isMiniplayerActive = false;

            document.getElementById('chipsBar').style.display = 'none';
            document.getElementById('videoGrid').style.display = 'none';
            document.getElementById('watchContainer').style.display = 'flex';
        }

        function closeMiniplayer() {
            const videoNode = document.getElementById('mainVideo');
            videoNode.pause();
            videoNode.src = "";
            document.getElementById('miniplayer').style.display = 'none';
            isMiniplayerActive = false;
        }

        function handleSuggestions(val) {
            const box = document.getElementById('suggestionsBox');
            if(!val.trim()) { box.style.display = 'none'; return; }
            
            const dummy = [`${val}`, `${val} live`, `${val} full song`, `${val} official video`];
            box.innerHTML = "";
            dummy.forEach(text => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `🔍 ${text}`;
                item.onclick = () => {
                    document.getElementById('queryInput').value = text;
                    executeSearch();
                };
                box.appendChild(item);
            });
            box.style.display = 'flex';
        }

        function setupKeyboardShortcuts() {
            window.addEventListener('keydown', (e) => {
                if(document.activeElement.tagName === 'INPUT') return;

                const vid = document.getElementById('mainVideo');

                if(e.code === 'Space' || e.code === 'KeyK') {
                    e.preventDefault();
                    vid.paused ? vid.play() : vid.pause();
                }

                if(e.code === 'ArrowLeft' || e.code === 'KeyJ') {
                    e.preventDefault();
                    vid.currentTime = Math.max(0, vid.currentTime - 5);
                }

                if(e.code === 'ArrowRight' || e.code === 'KeyL') {
                    e.preventDefault();
                    vid.currentTime = Math.min(vid.duration, vid.currentTime + 5);
                }

                if(e.code === 'ArrowUp') {
                    e.preventDefault();
                    vid.volume = Math.min(1, vid.volume + 0.1);
                }

                if(e.code === 'ArrowDown') {
                    e.preventDefault();
                    vid.volume = Math.max(0, vid.volume - 0.1);
                }

                if(e.code === 'KeyM') {
                    vid.muted = !vid.muted;
                }

                if(e.code === 'KeyF') {
                    if (document.fullscreenElement) {
                        document.exitFullscreen();
                    } else {
                        vid.requestFullscreen();
                    }
                }

                if(e.code === 'KeyI') {
                    if(isMiniplayerActive) {
                        maximizeFromMiniplayer();
                    } else if(activeVideo) {
                        minimizeToMiniplayer();
                    }
                }

                if(e.code.startsWith('Digit') && !e.shiftKey) {
                    const digit = parseInt(e.code.replace('Digit', ''));
                    if(!isNaN(digit) && vid.duration) {
                        vid.currentTime = (digit / 10) * vid.duration;
                    }
                }

                if(e.key === ',') {
                    vid.pause();
                    vid.currentTime = Math.max(0, vid.currentTime - (1/30));
                }
                if(e.key === '.') {
                    vid.pause();
                    vid.currentTime = Math.min(vid.duration, vid.currentTime + (1/30));
                }

                if(e.shiftKey && e.code === 'KeyN') {
                    if(activeVideo && currentQueue.length > 0) {
                        const currentIndex = currentQueue.findIndex(v => v.id === activeVideo.id);
                        if(currentIndex !== -1 && currentIndex + 1 < currentQueue.length) {
                            playVideo(currentQueue[currentIndex + 1].id);
                        }
                    }
                }

                if(e.key === '?' || (e.shiftKey && e.code === 'Slash')) {
                    toggleKeybindingsModal();
                }
            });
        }

        function showLoader(text) {
            document.getElementById('loader').style.display = 'flex';
            document.getElementById('loaderText').innerText = text;
        }

        function hideLoader() {
            document.getElementById('loader').style.display = 'none';
        }
    </script>
</body>
</html>
"""

def extract_video_id(query):
    query = query.strip()
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', query)
    if match: return match.group(1)
    if len(query) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', query):
        return query
    return query

def get_clean_youtube_url(query):
    v_id = extract_video_id(query)
    return f"https://www.youtube.com/watch?v={v_id}"

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/search', methods=['GET'])
def search_videos():
    query = request.args.get('q', 'Trending')
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'noplaylist': True,
        'user_agent': UA,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_res = ydl.extract_info(f"ytsearch12:{query}", download=False)
            results = []
            entries = json.loads(json.dumps(search_res.get('entries', [])))

            for entry in entries:
                video_id = entry.get('id')
                if not video_id: continue

                results.append({
                    'id': video_id,
                    'title': entry.get('title'),
                    'uploader': entry.get('uploader', 'NEXUS Channel'),
                    'thumbnail': f"/api/thumbnail?id={video_id}"
                })

            return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/thumbnail', methods=['GET'])
def proxy_thumbnail():
    video_id = request.args.get('id')
    if not video_id: return "Missing video ID", 400

    yt_thumb_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        res = requests.get(yt_thumb_url, headers=headers, timeout=5)
        return Response(res.content, status=res.status_code, content_type=res.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        return str(e), 500

@app.route('/api/stream-video', methods=['GET'])
def stream_video():
    query = request.args.get('q')
    if not query: return "Missing query", 400
    
    target_url = get_clean_youtube_url(query)
    ydl_opts = {
        'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
        'quiet': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')

            headers = {'User-Agent': ydl_opts['user_agent']}
            range_header = request.headers.get('Range', None)
            if range_header: headers['Range'] = range_header

            req = requests.get(video_url, headers=headers, stream=True)
            resp_headers = {k: v for k, v in req.headers.items() if k.lower() in ['content-type', 'content-length', 'content-range', 'accept-ranges']}

            def generate():
                for chunk in req.iter_content(chunk_size=1024 * 256):
                    if chunk: yield chunk

            return Response(stream_with_context(generate()), status=req.status_code, headers=resp_headers)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
