# AI Instagram Character Playbook

이 문서는 **AI로 운영되는 Instagram 캐릭터(고양이, 개, 사람 등)**를  
일관된 정체성, 시각적 유사도, 말투와 문맥을 유지하며 **반복적으로 생성**하기 위한 내부 가이드다.

이 프로젝트의 핵심은 **계정이 아니라 캐릭터**다.

---

## 0. 핵심 원칙 (NON-NEGOTIABLE)

1. 캐릭터는 파일로 관리되는 자산이다  
2. 캐릭터의 정체성은 DB가 아니라 설정 파일에 존재한다  
3. 이미지 유사도는 기능이 아니라 **정책**이다  
4. 시간이 지나도 “같은 인물”처럼 느껴지지 않으면 실패다  

---

## 1. 캐릭터 디렉토리 구조 (필수)

모든 캐릭터는 동일한 구조를 가진다.

```
characters/
└── <character_id>/
    ├── persona.toml
    ├── visual.toml
    ├── canon.toml
    ├── prompts/
    │   ├── image.txt
    │   └── caption.txt
    └── images/
        ├── ref_front.png
        ├── ref_side.png
        ├── ref_back.png
        ├── ref_full.png
        └── generated/
```

- `<character_id>` = 인스타 아이디와 동일
- 한 폴더 = 캐릭터 1명
- 다른 캐릭터는 복사 후 수정
- 스키마는 절대 제각각 만들지 말 것

---

## 2. Persona 작성 가이드 (`persona.toml`)

### 목적
- 캐릭터의 **말투, 사고방식, 태도**를 고정한다
- 어떤 문장을 생성해도 같은 인물처럼 들리게 한다

### 작성 원칙
- 성격 묘사보다 **행동 제약**이 중요
- “무엇을 하지 않는가”를 반드시 포함

### 좋은 예
```toml
[voice]
sentence_length = "short"
emoji_max = 1
questions_to_audience = false
```

### 나쁜 예
```toml
personality = "funny and cool"
```

---

## 3. Canon (세계관) 작성 가이드 (`canon.toml`)

### 목적
- 캐릭터가 절대 벗어나면 안 되는 사실 집합
- 농담보다 우선되는 규칙

### 작성 규칙
- 짧고 단정적인 문장
- 5~10개 이내
- 감정 표현 없음

### 예시
```toml
[[facts]]
text = "I am a real cat."

[[facts]]
text = "Posting is accidental."
```

---

## 4. Visual Identity 가이드 (`visual.toml`)

### 목적
- 캐릭터의 외형을 언어로 고정
- 이미지 생성 시 항상 참조

### 포함해야 할 요소
- 털 / 피부 패턴
- 색상
- 눈
- 체형
- 기본 표정

> Visual은 자주 바꾸지 않는다.  
> 바꾸는 순간 다른 캐릭터가 된다.

---

## 5. Reference Images 규칙

### 필수 레퍼런스
- ref_front.png  : 정면
- ref_side.png   : 측면
- ref_back.png   : 후면
- ref_full.png   : 전신

### 생성 규칙
- 반드시 photo-realistic
- 자연광
- 과장된 표정 금지
- 일러스트 / 만화 스타일 금지

> 이 이미지들은 캐릭터의 얼굴이다  
> Git LFS로 관리한다

---

## 6. 프로필 사진 생성 가이드 (후처리 X)

### 목표
- 인스타그램에서 허세 있어 보이되 과하지 않게
- 네모난 PNG (정사각형 필수 아님)

### 허용
- 선글라스
- 여유 있는 자세
- 미묘한 자신감

### 금지
- 만화 스타일
- 과한 패션 소품
- 과장된 표정

> 크롭, 원형 처리 등 후처리는 외부에서 수행

---

## 7. Caption / 문맥 작성 규칙

### 기본 규칙
- 실제 존재하는 캐릭터 일관성 유지.

---

## 8. 생성 파이프라인 (권장)

1. 캐릭터 폴더 로드
2. persona + canon → system prompt 생성
3. visual + ref images → image prompt 생성
4. 이미지 생성
5. 캡션 생성
6. 결과만 DB에 저장

> DB에는 결과만  
> 정체성은 파일에

---

## 9. 확장 시 주의사항

- 한 게시물에 하나의 persona만 사용
- 캐릭터 간 대화 시에도 각자 규칙 유지
- canon 변경은 신중히

---

## 10. 최종 요약

AI 인스타는 콘텐츠 제작이 아니다.  
**캐릭터를 설계하고 운영하는 일**이다.

캐릭터는  
- 설정으로 고정되고  
- 이미지로 기억되며  
- 말투로 살아남는다.