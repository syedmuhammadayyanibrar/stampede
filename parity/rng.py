import hashlib
from typing import Union
import numpy as np

class SeedManager:
    def __init__(self, master_seed: int = 42) -> None:
        self._master_seed = master_seed

    @property
    def master_seed(self) -> int:
        return self._master_seed

    def derive_seed(self, scope: str, sequence_id: Union[int, str] = 0) -> int:
        payload = f"{self._master_seed}:{scope}:{sequence_id}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return int(digest[:15], 16)

    def get_generator(self, scope: str, sequence_id: Union[int, str] = 0) -> np.random.Generator:
        derived = self.derive_seed(scope=scope, sequence_id=sequence_id)
        return np.random.default_rng(derived)

    def spawn(self, child_scope: str) -> "SeedManager":
        new_master = self.derive_seed(scope=child_scope, sequence_id="spawn")
        return SeedManager(master_seed=new_master)
