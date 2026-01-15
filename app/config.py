from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # OAuth 설정
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:3000/auth/callback/google"

    # JWT 설정
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # 데이터베이스 설정
    database_url: str = "sqlite:///database.db"

    # 애플리케이션 설정
    app_name: str = "BAPI"
    debug: bool = False


# 전역 설정 인스턴스
settings = Settings()
