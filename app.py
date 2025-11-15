from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import threading
import os
import time
import logging
import json

from agent import research_agent_workflow

app = Flask(__name__)

SESSION_LOG_DIR = os.path.join('sessions')
os.makedirs(SESSION_LOG_DIR, exist_ok=True)


def _attach_session_logger(session_id: str):
    """Attach a temporary file handler to the 'paper_agent' logger that writes to sessions/<session_id>.log"""
    logger = logging.getLogger('paper_agent')
    log_path = os.path.join(SESSION_LOG_DIR, f"{session_id}.log")
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return fh


def _detach_handler(handler):
    logger = logging.getLogger('paper_agent')
    try:
        logger.removeHandler(handler)
        handler.close()
    except Exception:
        pass


def _background_run(title: str, session_id: str, max_results: int):
    handler = _attach_session_logger(session_id)
    try:
        research_agent_workflow(title, session_id=session_id, max_results=max_results)
    finally:
        _detach_handler(handler)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run():
    title = request.form.get('title')
    session_id = request.form.get('session_id') or None
    max_results = int(request.form.get('max_results') or 5)
    if not title:
        return redirect(url_for('index'))

    # derive a session id if not provided
    session_id = session_id or f"job_{int(time.time())}"

    # start background thread
    t = threading.Thread(target=_background_run, args=(title, session_id, max_results), daemon=True)
    t.start()

    return redirect(url_for('status', session_id=session_id))


@app.route('/status/<session_id>')
def status(session_id):
    # shows a page with live log stream and a link to results when ready
    session_path = os.path.join('sessions', f"{session_id}.json")
    has_result = os.path.exists(session_path)
    return render_template('status.html', session_id=session_id, has_result=has_result)


@app.route('/stream/<session_id>')
def stream(session_id):
    log_path = os.path.join('sessions', f"{session_id}.log")

    def generate():
        # If file doesn't exist yet, wait until created
        last_pos = 0
        while True:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    f.seek(last_pos)
                    lines = f.read()
                    if lines:
                        for l in lines.splitlines():
                            yield f"data: {l}\n\n"
                        last_pos = f.tell()
            # check for completion
            if os.path.exists(os.path.join('sessions', f"{session_id}.json")):
                # indicate finished
                yield "data: __DONE__\n\n"
                break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.json or {}
    title = data.get('title')
    max_results = int(data.get('max_results', 5))
    if not title:
        return jsonify({'error': 'missing title'}), 400
    session_id = data.get('session_id') or f"job_{int(time.time())}"
    t = threading.Thread(target=_background_run, args=(title, session_id, max_results), daemon=True)
    t.start()
    return jsonify({'session_id': session_id})


@app.route('/result/<session_id>')
def result(session_id):
    # load session JSON when available
    path = os.path.join('sessions', f"{session_id}.json")
    if not os.path.exists(path):
        return redirect(url_for('status', session_id=session_id))
    with open(path, 'r', encoding='utf-8') as f:
        session = json.load(f)
    # reuse structure of research_agent_workflow result
    out = {'session_id': session_id, 'session': session, 'draft': session.get('draft',''), 'edited': session.get('edited',''), 'plagiarism': session.get('plagiarism',{})}
    return render_template('result.html', title=session.get('title',''), result=out)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
