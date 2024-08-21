from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GPT-Researcher"
    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    @property
    def GOOGLE_AUTH_URL(self):
        return (
            "https://accounts.google.com/o/oauth2/auth?"
            f"client_id={self.GOOGLE_CLIENT_ID}&"
            "response_type=code&"
            f"redirect_uri={self.GOOGLE_REDIRECT_URI}&"
            "scope=openid%20email%20profile"
        )
    class Config:
        env_file = ".env"

settings = Settings()