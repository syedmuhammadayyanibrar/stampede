# Stampede v1 Interface Specifications

This document defines the exact signatures, data classes, inputs, outputs, error conditions, and behavioral invariants of the v1 modules consumed by Parity.

---

## 1. Data Sources (`data_sources/openrouter.py`)

### `get_openrouter_api_key() -> str`
- **Inputs:** None. Reads `OPENROUTER_API_KEY` from `os.environ` or parses `.env` if present.
- **Outputs:** `str` containing the API key or empty string `""` if not found.
- **Exceptions:** Suppresses file errors when `.env` is absent.

### `fetch_rankings_daily(start_date: str, end_date: str, cache_dir: str = "data/openrouter_cache") -> List[Dict[str, Any]]`
- **Inputs:**
  - `start_date`: ISO format string `"YYYY-MM-DD"`.
  - `end_date`: ISO format string `"YYYY-MM-DD"`.
  - `cache_dir`: Local filesystem directory for JSON caching.
- **Outputs:** `List[Dict[str, Any]]` where each item contains:
  - `date`: `"YYYY-MM-DD"`
  - `model_permaslug`: e.g. `"anthropic/claude-3.5-sonnet"`
  - `total_tokens`: integer or numeric string representing daily volume
- **Exceptions:** Retries up to 4 times with exponential backoff on HTTP/JSON errors; returns empty list on total network failure if no cache exists.

---

## 2. Models & Data Classes (`models.py`)

### `ModelCalibration`
- **Dataclass Fields (`frozen=True`):**
  - `provider: str` (e.g. `"OpenAI"`, `"Anthropic"`)
  - `family_name: str` (e.g. `"GPT-4 / 4o Frontier Tier"`)
  - `spot_price_initial: float` (dollars per million tokens, e.g. `5.00`)
  - `annual_drift: float` (e.g. `-0.35`)
  - `annual_volatility: float` (e.g. `0.28`)
  - `hazard_rate_annual: float` (e.g. `1.85`)
  - `jump_mean: float` (e.g. `0.45`)
  - `base_spread: float` (e.g. `0.06`)
  - `shock_spread: float` (e.g. `0.38`)

### `MarketScenario`
- **Dataclass Fields:**
  - `switch_share: float = 0.60`
  - `switch_share_samples: Optional[np.ndarray] = None`
  - `absorbing_depth: float = 0.0`
  - `conversion_rate: float = 0.0`
  - `hazard_multiplier: Tuple[float, ...] = ()`
  - `utilization_samples: Optional[np.ndarray] = None`
  - `contract_type: str = "specific"`

### `LiquidityCalibration`
- **Dataclass Fields (`frozen=True`):**
  - `base_spread: float = 0.06`
  - `shock_spread_target: float = 0.38`
  - `impact_exponent: float = 0.5`
  - `daily_volume_ratio: float = 0.02`
  - `impact_constant: float = 0.75`

### `CALIBRATED_MODELS: Dict[str, ModelCalibration]`
- Pre-configured calibrations for `"openai_gpt_tier"` and `"anthropic_claude_tier"`.

---

## 3. Simulation Engine (`engine.py`)

### `SimulationResult`
- **Fields:**
  - `calibration: ModelCalibration`
  - `tenor_days: int`
  - `num_paths: int`
  - `time_steps: int`
  - `dt: float`
  - `time_grid: np.ndarray` (shape: `(steps + 1,)`)
  - `spot_paths: np.ndarray` (shape: `(num_paths, steps + 1)`)
  - `terminal_spot: np.ndarray` (shape: `(num_paths,)`)
  - `utilization: np.ndarray` (shape: `(num_paths,)`)
  - `shock_mask: np.ndarray` (shape: `(num_paths,)`, boolean)
  - `resale_spread: np.ndarray` (shape: `(num_paths,)`)
  - `realized_resale_price: np.ndarray` (shape: `(num_paths,)`)
  - `gross_value_buyer: np.ndarray` (shape: `(num_paths,)`)
  - `fair_forward_price: float`
  - `buyer_pnl: np.ndarray`
  - `seller_pnl: np.ndarray`
  - `standard_error: float`

### `run_monte_carlo(...) -> SimulationResult`
- **Inputs:**
  - `calibration: ModelCalibration`
  - `tenor_days: int`
  - `num_paths: int = 15000`
  - `resale_window_days: int = 14`
  - `risk_free_rate: float = 0.04`
  - `random_seed: int = 42`
  - `scenario: Optional[MarketScenario] = None`
  - `liquidity_cal: Optional[LiquidityCalibration] = None`
- **Outputs:** `SimulationResult` containing Monte Carlo geometric Brownian motion paths with Poisson jump-to-obsolescence.

---

## 4. Liquidity & Market Impact (`liquidity.py`)

### `compute_resale_spread(...) -> np.ndarray`
- **Inputs:**
  - `calibration: ModelCalibration`
  - `shock_mask: np.ndarray`
  - `utilization: np.ndarray`
  - `scenario: Optional[MarketScenario] = None`
  - `liquidity_cal: Optional[LiquidityCalibration] = None`
  - `rng: Optional[np.random.Generator] = None`
- **Outputs:** `np.ndarray` of realized half-spreads per path clipped to `[0.02, 0.85]`.
- **Behavior:** Implements square-root impact law $s = s_{\text{base}} + \kappa (\Delta V / V_{\text{daily}})^{\alpha}$.

---

## 5. Copilot Subsystem (`copilot/`)

### `parse_usage_csv(csv_content: str) -> UsageSummary` (`copilot/parser.py`)
- **Inputs:** CSV text payload.
- **Outputs:** `UsageSummary` (`success: bool`, `error: Optional[str]`, `dates: List[str]`, `daily_tokens_millions: List[float]`, `total_tokens_millions: float`, etc.).
- **Behavior:** Deterministic header matching for dates and token columns.

### `compute_optimal_contract_order(...) -> ContractRecommendation` (`copilot/sizing.py`)
- **Inputs:** `forecast: ForecastResult`, `spot_initial: float = 5.00`, `fair_fwd_price: float = 3.63`, `crunch_spread_pct: float = 0.358`.
- **Outputs:** `ContractRecommendation` with newsvendor optimal sizing $Q^*$ based on critical ratio $c_u / (c_u + c_o)$.

### `ground_numbers_check(text: str, allowed_values: List[float], rel_tol: float = 0.02) -> bool` (`copilot/explain.py`)
- **Inputs:** Generated text containing numbers, list of grounded allowed floats.
- **Outputs:** `bool` (`True` if all numbers in text are grounded or in default allowed set `{0, 1, 2, 3, 4, 5, 10, 14, 20, 30, 60, 90, 100, 365}`).
