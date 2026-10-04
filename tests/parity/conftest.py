import socket
import pytest

@pytest.fixture(autouse=True)
def block_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    original_connect = socket.socket.connect

    def guarded_connect(self, *args, **kwargs):
        raise RuntimeError("Outbound network access is strictly forbidden during pytest execution.")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
