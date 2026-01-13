from sqlmodel import Session, select
from app.models import Profile, Post, Chat, Message, ProfileChatLink
from app.database import engine, create_db_and_tables


def create_profiles():
    profiles_data = [
        {
            "name": "aria",
            "avatar": "https://i.postimg.cc/sXScNL2w/aria.png",
            "bio": "Product designer who loves minimalism and coffee.",
            "posts_count": 34,
            "followers_count": 1200,
            "following_count": 180,
        },
        {
            "name": "leos",
            "avatar": "https://example.com/avatars/leo.jpg",
            "bio": "Indie maker building small but useful products.",
            "posts_count": 23,
            "followers_count": 910,
            "following_count": 200,
        },
        {
            "name": "lincoln",
            "avatar": "https://i.postimg.cc/SjzsrvCh/lincoln.png",
            "bio": "16th President of the United States. Preserved the Union, abolished slavery.",
            "posts_count": 5,
            "followers_count": 1865000,
            "following_count": 1,
        },
        {
            "name": "newton",
            "avatar": "https://i.postimg.cc/C1R2S1yY/newton.png",
            "bio": "Physicist, mathematician, astronomer. Laid the foundations for classical mechanics.",
            "posts_count": 3,
            "followers_count": 1687000,
            "following_count": 0,
        },
        {
            "name": "sunsin",
            "avatar": "https://i.postimg.cc/vB7gXzY9/sunsin.png",
            "bio": "Korean admiral and military general famed for his victories against the Japanese navy.",
            "posts_count": 23,
            "followers_count": 1200000,
            "following_count": 0,
        },
    ]

    with Session(engine) as session:
        for profile_data in profiles_data:
            profile = Profile(**profile_data)
            session.add(profile)
        session.commit()


def create_posts():
    # 프로필 이름과 포스트 데이터 매핑
    posts_data = {
        "aria": [
            {
                "text": "오늘의 디자인 인사이트: 미니멀리즘의 진정한 의미는 단순함이 아닌 의도된 선택입니다.",
                "media_urls": ["https://example.com/aria/post1.jpg"],
            },
            {
                "text": "새로운 커피 레시피를 발견했어요! 에티오피아 원두로 만든 아이스 푸어 오버는 정말 특별하네요.",
                "media_urls": ["https://example.com/aria/post2.jpg"],
            },
            {
                "text": "디자인 시스템을 구축하면서 느낀 점: 일관성은 제품의 신뢰성을 높이는 핵심 요소입니다.",
                "media_urls": ["https://example.com/aria/post3.jpg"],
            },
        ],
        "leos": [
            {
                "text": "새로운 인디 프로젝트를 시작했습니다. 작은 도구지만 일상에 큰 변화를 줄 수 있기를 기대해요.",
                "media_urls": ["https://example.com/leos/post1.jpg"],
            },
            {
                "text": "사용자 피드백을 반영한 제품 업데이트를 출시했습니다. 항상 귀 기울여 주셔서 감사합니다!",
                "media_urls": ["https://example.com/leos/post2.jpg"],
            },
        ],
        "lincoln": [
            {
                "text": "국가를 위한 헌신은 때로 개인의 희생을 요구하지만, 그 가치는 항상 존재합니다.",
                "media_urls": ["https://example.com/lincoln/post1.jpg"],
            },
            {
                "text": "노예제 폐지에 대한 내 생각: 모든 인간은 자유를 누릴 권리가 있습니다.",
                "media_urls": ["https://example.com/lincoln/post2.jpg"],
            },
            {
                "text": "민주주의의 미래: 국민의 목소리가 국가의 방향을 결정해야 합니다.",
                "media_urls": ["https://example.com/lincoln/post3.jpg"],
            },
            {
                "text": "전쟁과 평화: 우리는 항상 평화를 향한 대화의 길을 선택해야 합니다.",
                "media_urls": ["https://example.com/lincoln/post4.jpg"],
            },
            {
                "text": "교육의 중요성: 지식은 민주주의의 기반입니다.",
                "media_urls": ["https://example.com/lincoln/post5.jpg"],
            },
        ],
        "newton": [
            {
                "text": "운동 법칙에 대한 새로운 통찰: 힘과 가속도의 관계는 우주의 근본 원리입니다.",
                "media_urls": ["https://example.com/newton/post1.jpg"],
            },
            {
                "text": "광학에 대한 연구: 빛의 성질을 이해하는 것은 자연 현상을 설명하는 열쇠입니다.",
                "media_urls": ["https://example.com/newton/post2.jpg"],
            },
            {
                "text": "미적분학의 발견: 수학은 자연을 설명하는 언어입니다.",
                "media_urls": ["https://example.com/newton/post3.jpg"],
            },
        ],
        "sunsin": [
            {
                "text": "임진왜란에서의 전략: 해전의 승리는 국가 안보의 핵심입니다.",
                "media_urls": ["https://example.com/sunsin/post1.jpg"],
            },
            {
                "text": "거북선의 장점: 이 혁신적인 전함은 우리 해군의 자랑입니다.",
                "media_urls": ["https://example.com/sunsin/post2.jpg"],
            },
            {
                "text": "군인의 사명: 나라를 지키는 것은 우리의 신성한 의무입니다.",
                "media_urls": ["https://example.com/sunsin/post3.jpg"],
            },
            {
                "text": "전략의 중요성: 무력 충돌에서 승리하기 위해서는 지혜로운 전략이 필요합니다.",
                "media_urls": ["https://example.com/sunsin/post4.jpg"],
            },
        ],
    }

    with Session(engine) as session:
        # 모든 프로필 가져오기
        profiles = session.exec(select(Profile)).all()

        # 프로필 이름으로 프로필 매핑
        profile_map = {profile.name: profile for profile in profiles}

        # 각 프로필에 대한 포스트 생성
        for profile_name, profile_posts in posts_data.items():
            if profile_name in profile_map:
                profile = profile_map[profile_name]
                for post_data in profile_posts:
                    post = Post(
                        text=post_data["text"],
                        media_urls=post_data["media_urls"],
                        profile_id=profile.id,
                    )
                    session.add(post)
        session.commit()


def create_chats():
    # 채팅 데이터 정의: 유저들 간의 다양한 조합
    chats_data = [
        {"name": "디자인에 대한 논의", "profile_names": ["aria", "leos"]},
        {"name": "역사와 리더십", "profile_names": ["lincoln", "sunsin"]},
        {
            "name": "과학과 전략의 만남",
            "profile_names": ["newton", "sunsin", "lincoln"],
        },
        {"name": "크리에이터 그룹", "profile_names": ["aria", "leos", "newton"]},
    ]

    with Session(engine) as session:
        # 모든 프로필 가져오기
        profiles = session.exec(select(Profile)).all()

        # 프로필 이름으로 프로필 매핑
        profile_map = {profile.name: profile for profile in profiles}

        # 각 채팅 생성
        for chat_data in chats_data:
            # 채팅 생성
            chat = Chat(name=chat_data["name"])
            session.add(chat)
            session.commit()
            session.refresh(chat)

            # 프로필들과 채팅 연결
            profile_names = chat_data["profile_names"]
            for profile_name in profile_names:
                if profile_name in profile_map:
                    profile = profile_map[profile_name]
                    link = ProfileChatLink(profile_id=profile.id, chat_id=chat.id)
                    session.add(link)
            session.commit()


def create_messages():
    # 메시지 데이터 정의: 각 채팅 내에서 유저들이 주고받은 메시지들
    messages_data = {
        "디자인에 대한 논의": [
            {"profile_name": "aria", "text": "안녕하세요! 디자인에 대해 이야기해보죠."},
            {
                "profile_name": "leos",
                "text": "좋은 생각이에요. 최근에 어떤 프로젝트 하셨나요?",
            },
            {
                "profile_name": "aria",
                "text": "미니멀한 인터페이스를 설계하고 있어요. 단순함이 핵심이죠.",
            },
            {
                "profile_name": "leos",
                "text": "그거 멋져요. 기능성과 아름다움의 균형이 중요하죠.",
            },
        ],
        "역사와 리더십": [
            {"profile_name": "lincoln", "text": "리더십이란 때로는 희생을 요구하지요."},
            {"profile_name": "sunsin", "text": "동의합니다. 하지만 전략도 중요합니다."},
            {
                "profile_name": "lincoln",
                "text": "전쟁에서의 승리는 국민을 지키는 데 중요하죠.",
            },
            {"profile_name": "sunsin", "text": "거북선이 바로 그런 전략의 산물입니다."},
            {"profile_name": "lincoln", "text": "혁신적인 사고가 승리로 이어지는군요."},
        ],
        "과학과 전략의 만남": [
            {"profile_name": "newton", "text": "자연의 법칙은 우주 전반에 적용됩니다."},
            {
                "profile_name": "sunsin",
                "text": "전략도 일종의 법칙이죠. 상대를 이해해야 합니다.",
            },
            {
                "profile_name": "lincoln",
                "text": "지식과 지혜가 결합할 때 위대한 일이 생깁니다.",
            },
            {
                "profile_name": "newton",
                "text": "과학적 접근은 전략 수립에 도움이 됩니다.",
            },
            {
                "profile_name": "sunsin",
                "text": "정확한 계산이 전투에서의 승리를 결정하죠.",
            },
        ],
        "크리에이터 그룹": [
            {
                "profile_name": "aria",
                "text": "새로운 디자인 툴을 찾고 있어요. 추천해 주세요!",
            },
            {
                "profile_name": "leos",
                "text": "저는 Figma를 주로 사용해요. 협업에 좋아요.",
            },
            {
                "profile_name": "newton",
                "text": "과학적 창의성도 중요하죠. 실험이 핵심입니다.",
            },
            {
                "profile_name": "aria",
                "text": "맞아요. 실패를 통해 배우는 것도 중요하죠.",
            },
            {
                "profile_name": "leos",
                "text": "사용자 피드백을 반영하는 것도 중요합니다.",
            },
        ],
    }

    with Session(engine) as session:
        # 모든 프로필 가져오기
        profiles = session.exec(select(Profile)).all()

        # 프로필 이름으로 프로필 매핑
        profile_map = {profile.name: profile for profile in profiles}

        # 모든 채팅 가져오기
        chats = session.exec(select(Chat)).all()

        # 채팅 이름으로 채팅 매핑
        chat_map = {chat.name: chat for chat in chats}

        # 각 채팅에 대한 메시지 생성
        for chat_name, chat_messages in messages_data.items():
            if chat_name in chat_map:
                chat = chat_map[chat_name]
                for message_data in chat_messages:
                    profile_name = message_data["profile_name"]
                    if profile_name in profile_map:
                        profile = profile_map[profile_name]
                        message = Message(
                            text=message_data["text"],
                            chat_id=chat.id,
                            profile_id=profile.id,
                        )
                        session.add(message)
        session.commit()


def main():
    create_db_and_tables()
    create_profiles()
    create_posts()
    create_chats()
    create_messages()


if __name__ == "__main__":
    main()
