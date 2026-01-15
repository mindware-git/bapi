import os
from PIL import Image
from typing import Tuple


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """
    이미지의 너비와 높이를 추출합니다.

    Args:
        image_path: 이미지 파일 경로

    Returns:
        Tuple[int, int]: (width, height)
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        print(f"Error getting image dimensions: {e}")
        return (0, 0)


def create_thumbnail(
    image_path: str, thumbnail_path: str, size: Tuple[int, int] = (160, 160)
) -> str:
    """
    이미지에서 160x160 썸네일을 생성합니다.
    원본 이미지의 비율을 유지하면서 중앙을 기준으로 크롭합니다.

    Args:
        image_path: 원본 이미지 파일 경로
        thumbnail_path: 썸네일 저장 경로
        size: 썸네일 크기 (기본값: 160x160)

    Returns:
        str: 생성된 썸네일 파일 경로
    """
    try:
        # 썸네일 저장 디렉토리 생성
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

        with Image.open(image_path) as img:
            # 이미지를 RGB 모드로 변환 (투명도 처리)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # 원본 이미지 비율 계산
            original_width, original_height = img.size
            original_ratio = original_width / original_height

            # 썸네일은 정사각형이므로 비율은 1
            target_ratio = 1.0

            # 크롭할 영역 계산
            if original_ratio > target_ratio:
                # 가로가 더 긴 이미지 (가로 사진)
                crop_height = original_height
                crop_width = int(crop_height * target_ratio)
                crop_left = (original_width - crop_width) // 2
                crop_top = 0
            else:
                # 세로가 더 긴 이미지 (세로 사진) 또는 정사각형
                crop_width = original_width
                crop_height = int(crop_width / target_ratio)
                crop_left = 0
                crop_top = (original_height - crop_height) // 2

            # 중앙에서 크롭
            crop_right = crop_left + crop_width
            crop_bottom = crop_top + crop_height
            cropped_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

            # 썸네일 크기로 리사이즈
            thumbnail_img = cropped_img.resize(size, Image.Resampling.LANCZOS)

            # 썸네일 저장 (품질 85%)
            thumbnail_img.save(thumbnail_path, "JPEG", quality=85, optimize=True)

        return thumbnail_path

    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        # 썸네일 생성 실패 시 원본 이미지를 썸네일로 복사
        try:
            import shutil

            shutil.copy2(image_path, thumbnail_path)
            return thumbnail_path
        except:
            return image_path
