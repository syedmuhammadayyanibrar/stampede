from stampede.sample import load_sample_prompts, get_sample_replay_notice, SAMPLE_QUOTES
from stampede.types import Provenance

def test_sample_replay_notice_and_provenance():
    notice = get_sample_replay_notice()
    assert notice.code == "REPLAYED_BENCHMARK_SAMPLE"
    assert "stored benchmark outputs" in notice.text
    prompts = load_sample_prompts()
    assert len(prompts) >= 20
    assert len(SAMPLE_QUOTES) == 3
