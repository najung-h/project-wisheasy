### 쉽길 커밋 컨벤션

쉽길 팀은 협업 시 일관된 코드 히스토리 관리와 가독성을 위해 **Angular Commit Convention**을 따릅니다. 

<br>

### 1. Commit Message Structure 

모든 커밋 메시지는 다음과 같은 형식을 따릅니다. 

<br>

```txt
type(scope): subject 

- body (optional) 

# footer (optional)
```

<br>

### 기본 형식

모든 커밋 메시지는 **`type(scope): subject`** 형식으로 시작합니다.

<br>

- **`type`**: 커밋의 성격을 나타내는 필수 항목입니다.
- **`scope`**: 커밋이 영향을 미치는 범위를 나타내는 선택적 항목입니다.
- **`subject`**: 변경 사항을 간결하게 설명하는 필수 항목입니다.

<br>

### 1. Type

<br>

커밋의 주요 목적을 나타내는 키워드입니다.

다음 목록을 사용하여 커밋의 의도를 명확하게 표현합시다.

<br>

- **`feat`**: 새로운 기능 추가 
- **`fix`**: 버그나 오류를 수정했을 때 
- **`docs`**: 문서(만) 수정 및 추가 
- **`design`**: UI/UX 관련 디자인 요소 변경 (CSS 등)
- **`refactor`**: 기능 변화 없이 코드 구조 개선
- **`build`** : 빌드 시스템이나 빌드 파일 수정
- **`ci`** : CI/CD 관련 설정 파일 수정
- **`chore`**: 기능과 관계없는 자잘한 수정
- **`rename`** : 파일 혹은 폴더명만 수정 한 경우
- **`remove`** : 파일 삭제만 한 경우

<br>

### 2. Scope 

(선택 사항) 변경이 발생한 모듈, 컴포넌트, 디렉토리 등 구체적인 범위를 명시합니다. 

<br>

**예시:**

- `feat(user-auth)`: 사용자 인증 관련 기능 추가
- `fix(payment)`: 결제 시스템의 버그 수정
- `docs(readme)`: `README.md` 문서 수정

<br>

### 3. Subject 

- 변경 사항을 간결하고 명확하게 요약합니다.

- 길이는 **50자 이내**로 작성합니다.

<br>

### + Body (본문)

- `Subject`로 표현할 수 없는 상세한 내용(해결 방법, 이유 등)을 설명하기 위해 작성합니다.
- 나의 작업 내용을 **다른 팀원이 커밋 메시지만 봐도 이해할 수 있도록** 적는 것이 목표입니다.

<br>

### + Footer (바닥글)

(선택 사항) 주로 관련된 이슈 번호를 언급하거나, **BREAKING CHANGE**와 같은 중요한 변경 사항을 명시할 때 사용합니다.

- **`BREAKING CHANGE`**: API 변경처럼 이전 버전과 호환되지 않는 변경이 있을 때 사용합니다.
- **`Closes`**, **`Fixes`**: 특정 이슈를 닫는 경우 사용합니다. `Closes #123` 또는 `Fixes #456`과 같이 작성합니다.

<br>

### 예시

<br>

```
feat: 로그인 API 연동 기능 추가
fix(payment): 결제 시스템 금액 오류 수정
docs: README 설치 방법 업데이트
design: 메인 페이지 다크모드 색상 적용
refactor: 중복된 유효성 검사 로직 함수 분리
chore: eslint 설정 업데이트
rename: app.js → main.js
remove: 불필요한 테스트 데이터 삭제
```

<br>

### 이미지

![](./images/git_graph.png)

