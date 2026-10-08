import sqlite3
from pathlib import Path
from stampede.sessions import SessionStore

def test_sentinel_erasure_on_session_delete(tmp_path):
    db_file = tmp_path / "test_meta.db"
    store = SessionStore(db_path=db_file)
    sess = store.create_session()
    sid = sess.session_id

    sentinel_prompt = "SECRET_SENTINEL_PROMPT_98765"
    sentinel_quote = "SECRET_SENTINEL_QUOTE_54321"

    sess.inputs["workload"] = [{"text": sentinel_prompt}]
    sess.inputs["quotes"] = [{"notes": sentinel_quote}]
    sess.session_cache["cache_key"] = {"output": sentinel_prompt}

    assert store.get_session(sid) is not None
    store.delete_session(sid)
    assert store.get_session(sid) is None

    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT * FROM session_meta WHERE session_id = ?", (sid,)).fetchall()
        assert len(rows) == 0

    content = db_file.read_bytes()
    assert sentinel_prompt.encode() not in content
    assert sentinel_quote.encode() not in content
