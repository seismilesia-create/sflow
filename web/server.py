from flask import Flask, render_template_string, request, jsonify


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SFlow - Transcription History</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0a0a0f;
            color: #e2e8f0;
            min-height: 100vh;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        header p {
            color: #64748b;
            font-size: 0.9rem;
        }

        .stats {
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
        }

        .stat-card {
            flex: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stat-card .number {
            font-size: 1.8rem;
            font-weight: 700;
            color: #818cf8;
        }

        .stat-card .label {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 4px;
        }

        .search-bar {
            margin-bottom: 24px;
        }

        .search-bar input {
            width: 100%;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: #e2e8f0;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-bar input:focus {
            border-color: #818cf8;
        }

        .search-bar input::placeholder {
            color: #475569;
        }

        .transcription-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .transcription-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 16px 20px;
            cursor: pointer;
            transition: background 0.2s, border-color 0.2s;
        }

        .transcription-item:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 255, 255, 0.12);
        }

        .transcription-item .meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .transcription-item .time {
            font-size: 0.8rem;
            color: #818cf8;
            font-weight: 500;
        }

        .transcription-item .duration {
            font-size: 0.75rem;
            color: #64748b;
            background: rgba(255, 255, 255, 0.05);
            padding: 2px 8px;
            border-radius: 6px;
        }

        .transcription-item .text {
            font-size: 0.95rem;
            line-height: 1.5;
            color: #cbd5e1;
        }

        .transcription-item .text.truncated {
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .transcription-item.expanded .text.truncated {
            display: block;
            -webkit-line-clamp: unset;
        }

        .transcription-item .actions {
            margin-top: 10px;
            display: flex;
            gap: 8px;
        }

        .btn-copy {
            font-size: 0.75rem;
            padding: 4px 12px;
            background: rgba(129, 140, 248, 0.15);
            color: #818cf8;
            border: 1px solid rgba(129, 140, 248, 0.3);
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .btn-copy:hover {
            background: rgba(129, 140, 248, 0.25);
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #475569;
        }

        .empty-state p {
            font-size: 1.1rem;
            margin-bottom: 8px;
        }

        .empty-state small {
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SFlow</h1>
            <p>Voice-to-Text Transcription History</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="number" id="totalCount">-</div>
                <div class="label">Total Transcriptions</div>
            </div>
            <div class="stat-card">
                <div class="number" id="todayCount">-</div>
                <div class="label">Today</div>
            </div>
        </div>

        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search transcriptions...">
        </div>

        <div class="transcription-list" id="transcriptionList">
            <div class="empty-state">
                <p>No transcriptions yet</p>
                <small>Press Ctrl+Shift (hold) or double-tap Ctrl to start recording</small>
            </div>
        </div>
    </div>

    <script>
        let searchTimeout;

        async function loadTranscriptions(query = '') {
            const url = query ? `/api/search?q=${encodeURIComponent(query)}` : '/api/transcriptions';
            const resp = await fetch(url);
            const data = await resp.json();
            renderTranscriptions(data.transcriptions || []);
        }

        async function loadStats() {
            const resp = await fetch('/api/stats');
            const data = await resp.json();
            document.getElementById('totalCount').textContent = data.total || 0;
            document.getElementById('todayCount').textContent = data.today || 0;
        }

        function renderTranscriptions(items) {
            const list = document.getElementById('transcriptionList');
            if (!items.length) {
                list.innerHTML = `
                    <div class="empty-state">
                        <p>No transcriptions found</p>
                        <small>Press Ctrl+Shift (hold) or double-tap Ctrl to start recording</small>
                    </div>`;
                return;
            }

            list.innerHTML = items.map(item => {
                const date = new Date(item.created_at + 'Z');
                const timeStr = date.toLocaleString();
                const dur = item.duration_seconds ? item.duration_seconds.toFixed(1) + 's' : '';
                return `
                    <div class="transcription-item" onclick="this.classList.toggle('expanded')">
                        <div class="meta">
                            <span class="time">${timeStr}</span>
                            ${dur ? `<span class="duration">${dur}</span>` : ''}
                        </div>
                        <div class="text truncated">${escapeHtml(item.text)}</div>
                        <div class="actions">
                            <button class="btn-copy" onclick="event.stopPropagation(); copyText('${escapeJs(item.text)}')">Copy</button>
                        </div>
                    </div>`;
            }).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function escapeJs(text) {
            return text.replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/\\n/g, '\\\\n');
        }

        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                // Visual feedback could be added here
            });
        }

        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => loadTranscriptions(e.target.value), 300);
        });

        // Initial load + auto-refresh
        loadTranscriptions();
        loadStats();
        setInterval(() => {
            const query = document.getElementById('searchInput').value;
            loadTranscriptions(query);
            loadStats();
        }, 5000);
    </script>
</body>
</html>
"""


def create_app(db):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/transcriptions")
    def api_transcriptions():
        limit = request.args.get("limit", 50, type=int)
        transcriptions = db.get_recent(limit=limit)
        return jsonify({"transcriptions": transcriptions})

    @app.route("/api/search")
    def api_search():
        query = request.args.get("q", "")
        if not query:
            return jsonify({"transcriptions": []})
        transcriptions = db.search(query=query)
        return jsonify({"transcriptions": transcriptions})

    @app.route("/api/stats")
    def api_stats():
        total = db.count()
        # Contar transcripciones de hoy
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        today_count = conn.execute(
            "SELECT COUNT(*) FROM transcriptions WHERE date(created_at) = date('now')"
        ).fetchone()[0]
        conn.close()
        return jsonify({"total": total, "today": today_count})

    return app
