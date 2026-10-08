from stampede.events import EventLog

def test_event_log_sequence_and_sse_formatting():
    log = EventLog()
    e1 = log.emit("stage_start", "ingest", {"step": 1})
    e2 = log.emit("stage_complete", "ingest", {"rows": 90})
    assert e1.seq == 1
    assert e2.seq == 2
    assert "id: 1\n" in e1.to_sse_format()
    assert "event: stage_start\n" in e1.to_sse_format()

def test_last_event_id_resume():
    log = EventLog()
    for i in range(1, 6):
        log.emit("stage_step", "parity", {"index": i})
    assert len(log.get_events_since(None)) == 5
    resumed = log.get_events_since(3)
    assert len(resumed) == 2
    assert resumed[0].seq == 4
    assert resumed[1].seq == 5
