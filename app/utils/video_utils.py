import os
import shutil
from typing import Tuple


def get_video_metadata(video_path: str) -> Tuple[int, int, int, str]:
    """
    Mock 함수: 비디오 메타데이터 추출
    FFmpeg가 설치되지 않은 상황에서 테스트를 위해 mock 데이터 반환

    Args:
        video_path: 비디오 파일 경로

    Returns:
        Tuple[int, int, int, str]: (duration, width, height, codec)
        - duration: 비디오 길이 (초)
        - width: 비디오 너비
        - height: 비디오 높이
        - codec: 비디오 코덱
    """
    # Mock 데이터 반환 (나중에 FFmpeg로 실제 구현 필요)
    return (30, 1920, 1080, "h264")


def create_video_thumbnail(video_path: str, thumbnail_path: str) -> str:
    """
    Mock 함수: 비디오 썸네일 생성
    FFmpeg가 설치되지 않은 상황에서 테스트를 위해 기존 이미지 썸네일 복사

    Args:
        video_path: 비디오 파일 경로
        thumbnail_path: 썸네일 저장 경로

    Returns:
        str: 생성된 썸네일 파일 경로
    """
    # 썸네일 저장 디렉토리 생성
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

    # 기존 이미지 썸네일을 복사하여 사용 (mock)
    # 나중에 FFmpeg로 실제 비디오 썸네일 생성 필요
    default_thumbnail = "app/static/images/originals/default_avatar.png"

    if os.path.exists(default_thumbnail):
        shutil.copy2(default_thumbnail, thumbnail_path)
    else:
        # 기본 썸네일이 없으면 빈 파일 생성
        with open(thumbnail_path, "wb") as f:
            f.write(b"")

    return thumbnail_path
