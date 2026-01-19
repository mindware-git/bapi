AI Instagram Character Playbook

이 문서는 **AI로 운영되는 Instagram 캐릭터(고양이, 개, 사람 등)**를
일관된 정체성, 시각적 유사도, 말투와 문맥을 유지하며
반복적으로 생성·운영하기 위한 내부 가이드다.

이 프로젝트의 핵심 단위는 계정이 아니라 캐릭터다.

⸻

0. 핵심 원칙 (NON-NEGOTIABLE)
	1.	캐릭터는 코드가 아니라 파일 자산이다
	2.	캐릭터의 정체성은 DB가 아니라 설정 파일에 존재한다
	3.	이미지 유사도는 기능이 아니라 정책이다
	4.	시간이 지나도 “같은 인물”처럼 느껴지지 않으면 실패다

⸻

1. 캐릭터 디렉토리 구조 (실제 사용 구조)

모든 캐릭터는 아래 구조를 그대로 따른다.

characters/
└── <character_id>/
    ├── persona.toml
    ├── visual.toml
    ├── canon.toml
    ├── profile.png
    ├── images/
    │   ├── ref_front.png
    │   ├── ref_side.png
    │   ├── ref_back.png
    │   └── ref_full.png
    ├── prompts/
    │   └── image_base.txt
    └── posts/
        └── <post_id>/
            ├── <index>.png
            ├── <index>.txt   (optional)
            └── meta.toml

기본 규칙
	•	<character_id> = Instagram 아이디와 동일
	•	한 폴더 = 캐릭터 1명
	•	다른 캐릭터는 복사 후 수정
	•	구조를 임의로 변경하지 않는다

⸻

2. Persona 작성 가이드 (persona.toml)

목적
	•	캐릭터의 말투, 문장 길이, 태도를 고정
	•	어떤 캡션을 생성해도 같은 인물처럼 들리게 함

작성 원칙
	•	성격 묘사 ❌
	•	행동 제약 / 금지 규칙 ⭕

⸻

3. Canon 작성 가이드 (canon.toml)

목적
	•	캐릭터가 절대 벗어나면 안 되는 세계관의 법칙

규칙
	•	짧고 단정적인 문장
	•	5~10개 권장
	•	감정 표현 없음

⸻

4. Visual Identity 가이드 (visual.toml)

목적
	•	캐릭터의 외형을 언어로 고정
	•	이미지 생성 시 항상 참조되는 단일 진실

Visual을 바꾸는 순간
다른 캐릭터가 된다

⸻

5. Reference Images 규칙 (images/ref_*.png)

필수 레퍼런스
	•	ref_front.png : 정면
	•	ref_side.png  : 측면
	•	ref_back.png  : 후면
	•	ref_full.png  : 전신

규칙
	•	반드시 photo-realistic
	•	자연광
	•	과장된 표정 ❌
	•	만화 / 일러스트 스타일 ❌
	•	Git LFS로 관리

⸻

6. 프로필 사진 생성 가이드 (profile.png)

목표
	•	Instagram 프로필용 원본 이미지

규칙
	•	반드시 photo-realistic
	•	중앙 크롭 대비 → 캐릭터는 화면 중앙
	•	PNG
	•	원형 / 라운드 엣지 ❌
	•	모든 후처리는 외부에서 수행

저장 위치

characters/<character_id>/profile.png


⸻

7. Image Base Prompt (prompts/image_base.txt)

목적
	•	촬영 현실성 정책 고정
	•	외형 설명 ❌
	•	상황 설명 ❌

외형은 visual.toml
상황은 post의 <index>.txt

⸻

8. Posts 디렉토리 규칙 (posts/)

각 포스트는 실제 Instagram 게시물 1개에 대응된다.
포스트는 콘텐츠가 아니라 캐릭터의 활동 로그다.

디렉토리 구조

posts/<post_id>/
├── <index>.png
├── <index>.txt   (optional)
└── meta.toml


⸻

기본 규칙
	•	이미지 최소 1장 필수
	•	텍스트는 선택
	•	이미지 없는 포스트 ❌
	•	하나의 포스트 = 하나의 상황

⸻

이미지 파일 (<index>.png)
	•	실제 업로드되는 결과 이미지
	•	파일명은 순서만 의미

1.png
2.png



⸻

이미지 보조 프롬프트 (<index>.txt)
	•	해당 이미지 한 장에만 적용되는 추가 지시
	•	없으면 기본 설정만 사용

예:

Slightly closer framing.
More focus on the eyes.


⸻

meta.toml — 의미 레이어
	•	이 포스트가 왜 존재하는지
	•	감정, 맥락, 의도
	•	이미지 생성에는 직접 사용 ❌

⸻

9. 포스트 작성 철학
	•	웃긴 것도 가능
	•	슬픈 것도 가능
	•	중요한 것은 캐릭터의 색 유지
	•	포스트는 캐릭터의 일기다

⸻

10. DB와의 관계
	•	characters/ : 정체성의 원본
	•	DB : 결과만 저장

DB 저장 대상:
	•	character_id
	•	post_id
	•	image_paths
	•	text (있을 경우)
	•	timestamp

정체성은 파일에
DB는 결과만
