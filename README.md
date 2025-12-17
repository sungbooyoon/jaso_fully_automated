# jaso_fully_automated 
## 맨날 고통받다 만든 완전히 자동화된 macOS 한글 자소분리 자동 방지 데몬

기존에 맥에서 한글 파일명 자소분리(NFD) 문제 해결하는 솔루션들이 많은데, 다 컴퓨터를 켜고 뭔가를 해야하는 것들이었다.
진짜 딱 한번만 설정하면 평생 아무것도 안해도 되는 완전히 자동화된(fully automated) 걸 만들고 싶었음.

### 주요 특징
- 메뉴바 앱 ❌
- 유료 어플 ❌
- 모든 하위 폴더 재귀 감시 ✅
- 로그인 시 자동 실행 ✅

## 1. 설치

```bash
cd ~
git clone https://github.com/sungbooyoon/jaso_fully_automated.git
cd jaso_fully_automated
poetry init -n
poetry add watchdog
poetry install
```

---

## 2. 수동 실행 테스트

### 2.1 WATCH_DIRECTORY 수정

🚨 `jaso.py` 안에 `WATCH_DIRECTORY`를 **내가 자소분리를 자동으로 방지할 폴더**로 설정한다.
나같은 경우는 "/Users/sungbooyoon"로 설정.

### 2.2 터미널에서 정상 실행 확인

```bash
poetry run python jaso.py
```

- 에러 없이 실행되면 정상
- 중지: `Ctrl + C`

---

## 3. 로그인 시 자동 실행 설정 (Automator)

### 3.1 Automator Application 생성

1. Automator 실행
2. 새 문서 → 응용 프로그램(Application)

### 3.2 쉘 스크립트 실행 (Run Shell Script) 추가

- 쉘: `/bin/zsh` (혹은 기본값)
- 입력 전달: 상관없음(아무거나)

### 3.3 Run Shell Script 내용

🚨 `JASO_DIR` 를 git clone한 경로 (ex. "/Users/sungboo/jaso_fully_automated")로 변경한다.
🚨 `#!/bin/zsh` 필요시 수정

```bash
#!/bin/zsh # 필요시 수정

JASO_DIR="" # git clone한 경로 (ex. "/Users/sungboo/jaso_fully_automated")
POETRY="/opt/homebrew/bin/poetry" # which poetry 로 확인한 경로
LOGDIR="$HOME/Library/Logs/jaso"

mkdir -p "$LOGDIR"
cd "$JASO_DIR" || exit 1

if pgrep -f "python.*jaso.py" >/dev/null 2>&1; then
  exit 0
fi

nohup "$POETRY" run python jaso.py \
  >> "$LOGDIR/stdout.log" \
  2>> "$LOGDIR/stderr.log" &

exit 0
```

### 3.4 에러 로그 확인(선택)

Automator에서 실행을 누르고, 터미널을 열고 아래 커맨드를 실행한다.

```bash
tail -n 50 ~/Library/Logs/jaso/stderr.log
```
- 에러 없이 실행되면 정상


### 3.5 저장

어플리케이션으로 저장 ex. `Jaso.app`

---

## 4. 로그인 항목(Login Item) 등록

시스템 설정 → 일반 → 로그인 항목 → `Jaso.app` 추가

---

## 참고 사이트

- https://disquiet.io/@hsol/makerlog/%EB%A7%A5os-%ED%95%9C%EA%B8%80-%EC%9E%90%EC%86%8C%EB%B6%84%EB%A6%AC-%ED%98%84%EC%83%81-%EC%9E%90%EB%8F%99%EB%B3%80%ED%99%98-%ED%94%84%EB%A1%9C%EA%B7%B8%EB%9E%A8-nfd-nfc
