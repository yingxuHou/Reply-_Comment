from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "reply-comment-agent"
    env: str = "dev"
    database_url: str = "sqlite:///./data/app.db"

    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm_chat_model: str = "glm-4"
    glm_embed_model: str = "embedding-2"

    vector_dir: str = "./data/vectors"
    default_kb_slug: str = "default"


settings = Settings()

