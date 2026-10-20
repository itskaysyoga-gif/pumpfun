"""Settings loaded from the environment / .env.

The live-trading guard lives here so no other module can decide on its own
that real money may move."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rpc_ws_url: str = "wss://api.mainnet-beta.solana.com"
    rpc_http_url: str = "https://api.mainnet-beta.solana.com"
    data_dir: Path = Path("./data")

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    live: bool = False
    wallet_pubkey: str = ""
    # The burner wallet's public address, set in config only once Phase 7 is approved.
    approved_burner_pubkey: str = ""

    @property
    def live_trading_enabled(self) -> bool:
        """True only when every guard agrees. Anything else means simulate."""
        return (
            self.live
            and bool(self.wallet_pubkey)
            and bool(self.approved_burner_pubkey)
            and self.wallet_pubkey == self.approved_burner_pubkey
        )


def load() -> Settings:
    return Settings()
