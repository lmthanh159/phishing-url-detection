"""Application configuration — paths, constants, artifact loading."""
import json
import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_dir: str = os.getenv("MODEL_DIR", str(Path(__file__).resolve().parent.parent.parent / "artifacts"))
    app_name: str = "Phishing URL Detection API"
    max_url_length: int = 8192
    max_batch_size: int = 1000
    max_batch_file_mb: int = 5
    log_dir: str = "logs"

    @property
    def model_path(self) -> Path:
        return Path(self.model_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── Risk level bands (independent of threshold) ──
RISK_LEVEL_BANDS = [
    (0.00, 0.30, "low"),
    (0.30, 0.60, "medium"),
    (0.60, 0.85, "high"),
    (0.85, 1.01, "critical"),
]

# ── Suspicious TLDs ──
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "club", "work",
    "date", "loan", "racing", "win", "bid", "stream", "download",
    "click", "link", "gdn", "men", "review", "country", "kim",
    "science", "party", "cricket", "accountant", "faith", "zip", "mov",
}

# ── URL shortener domains ──
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co", "is.gd",
    "buff.ly", "adf.ly", "tiny.cc", "lnkd.in", "db.tt", "qr.ae",
    "rebrand.ly", "bl.ink", "short.io",
}

# ── Suspicious keywords ──
SUSPICIOUS_KEYWORDS = {
    "login": ["login", "log-in", "log_in", "signin", "sign-in", "sign_in", "signon"],
    "verify": ["verify", "verification", "validate", "confirm", "confirmation"],
    "account": ["account", "myaccount", "my-account", "useraccount"],
    "secure": ["secure", "security", "ssl", "safe", "protection"],
    "bank": ["bank", "banking", "onlinebanking"],
    "update": ["update", "upgrade", "renew", "renewal"],
    "payment": ["payment", "pay", "billing", "invoice", "transaction"],
    "free": ["free", "bonus", "reward", "prize", "winner", "gift"],
}

# ── Brand similarity thresholds ──
BRAND_SIMILARITY_THRESHOLD = 80
BRAND_MIN_TOKEN_LENGTH = 4


def load_json_artifact(filename: str) -> dict | list:
    """Load a JSON artifact from the model directory."""
    path = get_settings().model_path / filename
    with open(path) as f:
        return json.load(f)


@lru_cache
def get_brand_list() -> list[str]:
    return load_json_artifact("brand_list.json")


@lru_cache
def get_brand_official_domains() -> dict[str, list[str]]:
    """Official domains for brands — hardcoded since not in artifacts."""
    return {
        "paypal": ["paypal.com"], "google": ["google.com", "gmail.com", "googleapis.com"],
        "facebook": ["facebook.com", "fb.com"], "apple": ["apple.com", "icloud.com"],
        "microsoft": ["microsoft.com", "live.com", "outlook.com", "office.com"],
        "amazon": ["amazon.com"], "netflix": ["netflix.com"], "instagram": ["instagram.com"],
        "github": ["github.com", "github.io"], "linkedin": ["linkedin.com"],
        "twitter": ["twitter.com", "x.com"], "steam": ["steampowered.com", "steamcommunity.com"],
    }


@lru_cache
def get_feature_schema() -> dict:
    return load_json_artifact("feature_schema.json")


@lru_cache
def get_shared_infra_domains() -> dict:
    return load_json_artifact("shared_infra_domains.json")


@lru_cache
def get_threshold_config() -> dict:
    return load_json_artifact("threshold_config.json")


@lru_cache
def get_model_metadata() -> dict:
    return load_json_artifact("model_metadata.json")
