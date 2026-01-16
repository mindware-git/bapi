from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from typing import Annotated
import requests
from datetime import datetime, timezone, timedelta
from app.database import get_session
from app.models.user import User, OAuthAccount
from app.models.profile import Profile
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_infos_from_google_token(code: str) -> dict:
    """구글 OAuth 코드로 사용자 정보 가져오기"""
    try:
        # 코드를 액세스 토큰으로 교환
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        token_data = token_response.json()
        if "error" in token_data:
            return {"status": False, "user_infos": None, "error": token_data}

        access_token = token_data.get("access_token")

        if not access_token:
            return {
                "status": False,
                "user_infos": None,
                "error": "No access token received",
            }

        # 액세스 토큰으로 사용자 정보 조회
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        user_info = user_info_response.json()

        return {
            "status": bool(user_info and "id" in user_info),
            "user_infos": user_info,
            "token_data": token_data,
        }

    except Exception as e:
        return {"status": False, "user_infos": None, "error": str(e)}


@router.post("/callback/google")
async def google_callback(
    code: str, session: Annotated[Session, Depends(get_session)]
) -> dict:
    """구글 OAuth 콜백 처리 - 사용자 가입만 처리"""
    try:
        # 실제 구글 API로 사용자 정보 가져오기
        google_result = get_user_infos_from_google_token(code)

        if not google_result["status"]:
            error_detail = google_result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info from Google: {error_detail}",
            )

        google_user_info = google_result["user_infos"]
        token_data = google_result["token_data"]

        # 기존 OAuth 계정 확인
        oauth_account = session.exec(
            select(OAuthAccount).where(
                OAuthAccount.oauth_provider == "google",
                OAuthAccount.provider_user_id == google_user_info["id"],
            )
        ).first()

        if oauth_account:
            # 기존 사용자
            user = oauth_account.user
            message = "Existing user signed in successfully"

            # OAuth 토큰 정보 업데이트
            oauth_account.access_token = token_data.get("access_token")
            oauth_account.refresh_token = token_data.get("refresh_token")
            oauth_account.expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )
        else:  # OAuth 계정이 없는 경우 (신규 사용자 또는 기존 사용자에 OAuth 연결)
            # 이메일로 기존 사용자 확인
            existing_user = session.exec(
                select(User).where(User.email == google_user_info["email"])
            ).first()

            if existing_user:
                user = existing_user
                message = "Existing user linked with Google account"
            else:
                profile = Profile(name=google_user_info["email"])
                user = User(email=google_user_info["email"], profile_id=profile.id)
                session.add(user)
                message = "New user created successfully"

            # OAuth 계정 연결
            oauth_account = OAuthAccount(
                user_id=user.id,
                oauth_provider="google",
                provider_user_id=google_user_info["id"],
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                expires_at=datetime.now(timezone.utc)
                + timedelta(seconds=token_data.get("expires_in", 3600)),
                token_type=token_data.get("token_type"),
                scope=token_data.get("scope"),
            )
            session.add(oauth_account)

        session.commit()

        return {
            "message": message,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}",
        )
