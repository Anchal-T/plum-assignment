from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Plum OPD Adjudicator"
    debug: bool = False

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    policy_file: str = "policy_terms.json"

    fraud_same_day_threshold: int = 2
    fraud_frequency_threshold: int = 5
    fraud_frequency_window_days: int = 30
    manual_review_amount_threshold: float = 25000.0
    confidence_threshold: float = 0.70

    class Config:
        env_file = ".env"


settings = Settings()
