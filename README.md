# PROJECT_wisheasy

#  



# 지하철 역사 내 에스컬레이터 기반 경로 안내 서비스

## 서비스 소개
본 서비스는 **지하철 역사 내 이동 경로를 스토리 카드 형식으로 안내**하는 시스템입니다.  
사용자가 출발역과 도착역을 입력하면, 해당 역사에 운영 중인 **에스컬레이터 위치와 역 구조 정보**를 바탕으로  
에스컬레이터 최적의 이동 동선을 단계별로 제공합니다.  

특히 초행길 이용자도 직관적으로 따라갈 수 있도록 스토리 카드 형식의 안내를 제공하여  
**더 쉽고, 더 편안한 지하철 경험**을 보장합니다.

---

## 핵심 가치
- 🚇 **에스컬레이터 최적 활용**  
  역사 내 운영 중인 에스컬레이터 정보를 반영하여, 이용 가능한 에스컬레이터를 놓치지 않도록 안내합니다.

- 🗺️ **역사 내 상세 경로 제공**  
  단순한 출발-도착 정보가 아닌, 역사 내부 이동 경로까지 고려한 단계별 안내를 제공합니다.

- 🏪 **편의시설 정보 제공**  
  화장실, 환승 통로, 편의점 등 역사 내 편의시설 정보를 함께 제공하여 이용 편의를 높입니다.

- 📱 **스토리 카드 형식 안내**  
  단계별 동선 안내를 카드 형식으로 제공하여 직관적이고 쉽게 따라갈 수 있습니다.

---

## 기대 효과
- 초행길 이용자도 길을 잃지 않고 **편리하게 역사 내 이동 가능**
- 노약자, 어린이 동반, 캐리어 이용객 등 **이동 약자의 접근성 개선**
- 단순한 길 안내를 넘어, **쾌적하고 편안한 지하철 경험** 제공

---

## 사용 예시
1. 출발역과 도착역 입력  
2. 에스컬레이터 위치 및 역사 구조 기반 경로 생성  
3. 스토리 카드 형식으로 단계별 안내 제공  

<br><br>

# 팀원소개
<table>
  <tr>
    <td align="center" width="200px">
      <a href="./docs/trouble_shooting/나정현.md"> <img src="./doc/images/worry_bubble.svg" alt="말풍선1" width="100%" />
      </a>
    </td>
    <td align="center" width="200px">
      <a href="./docs/trouble_shooting/박준아.md">
        <img src="./doc/images/worry_bubble.svg" alt="말풍선2" width="100%" />
      </a>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/najung-h.png" width="100px" style="border-radius: 50%;" />
      <br />
      <b>나정현</b> <br> (PM, Infra CI/CD)
    </td>
    <td align="center">
      <img src="https://github.com/ajjoona-git.png" width="100px" style="border-radius: 50%;" />
      <br />
      <b>박준아</b> <br> (UI/UX, Frontend)
    </td>
  </tr>
</table>
<table>
  <tr>
    <td align="center" width="200">
      <a href="./docs/trouble_shooting/김소희.md">
        <img src="./doc/images/worry_bubble.svg" alt="고민1" width="100%" />
      </a>
    </td>
    <td align="center" width="200">
      <a href="./docs/trouble_shooting/정환승.md">
        <img src="./doc/images/worry_bubble.svg" alt="고민2" width="100%" />
      </a>
    </td>
    <td align="center" width="200">
      <a href="./docs/trouble_shooting/박지연.md">
        <img src="./doc/images/worry_bubble.svg" alt="고민3" width="100%" />
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="200">
      <img src="https://github.com/hann2a.png" width="80px" style="border-radius: 50%;" />
      <br />
      <b>팀원1</b> <br> (Backend)
    </td>
    <td align="center" width="200">
      <img src="https://github.com/hwanseung251.png" width="80px" style="border-radius: 50%;" />
      <br />
      <b>팀원2</b> <br> (Frontend)
    </td>
    <td align="center" width="200">
      <img src="https://github.com/yeonliyou.png" width="80px" style="border-radius: 50%;" />
      <br />
      <b>팀원3</b> <br> (Infra)
    </td>
  </tr>
</table>

### 1) 아키텍처 개요 (Flowchart)

<br>

```mermaid
flowchart LR
  %% ===== Clusters =====
  subgraph Dev["Developer & CI/CD (dev & PR)"]
    A[Developer<br/>push to dev / open PR]
    subgraph GHA["GitHub Actions"]
      B[Build & Push<br/>docker/build-push-action]
      D["Deploy via SSH<br/>appleboy/ssh-action<br/>(push:dev only)"]
    end
    HUB["(Docker Hub<br/>wisheasy:latest, sha-<commit>)"]
  end

  subgraph EC2["AWS EC2 (Ubuntu host)"]
    subgraph DB["MySQL (mysql:8.0)"]
      M1["mysql_db<br/>healthcheck OK"]
    end
    subgraph WEB["Web (Django + Gunicorn)"]
      W1["wisheasy_web<br/>0.0.0.0:8000<br/>env: .env"]
    end
    subgraph EDGE["Nginx (edge)"]
      N1["listen 80 → 301 → 443<br/>server_name wisheasy.site<br/>/static → /app/staticfiles"]
    end
    SF[(./staticfiles)]
    LG[(./logs)]
    VD[(app_data volume)]
  end

  EXT["(Let's Encrypt<br/>/etc/letsencrypt)"]
  U["User (Browser)"]

  %% ===== Flows =====
  A -->|push dev / PR| B
  B -->|push image<br/>latest + sha| HUB
  B --> D
  D -->|SSH| EC2
  HUB -. compose pull .-> W1

  %% Inbound traffic
  U -->|"HTTP 80 / HTTPS 443"| N1
  N1 -->|proxy_pass http://web:8000| W1
  W1 -->|TCP 3306| M1

  %% Volumes / mounts
  N1 --- SF
  W1 --- SF
  W1 --- LG
  W1 --- VD
  N1 --- EXT

  %% Notes
  classDef note fill:#fff,stroke:#bbb,stroke-dasharray:3 3,color:#333;
```

### <br><br><br><br>2) 배포 파이프라인(Sequence)

<br>

```mermaid
sequenceDiagram
  autonumber
  participant Dev as Developer
  participant GHA as GitHub Actions
  participant Hub as Docker Hub
  participant EC2 as EC2 Host
  participant DB as mysql_db
  participant Web as wisheasy_web
  participant Nginx as Nginx(edge)

  Dev->>GHA: push to dev / open PR
  alt pull_request to dev
    GHA->>GHA: Lint/Build (no deploy)
    GHA-->>Dev: CI result (checks)
  else push to dev
    GHA->>GHA: Buildx build
    GHA->>Hub: Push image (latest & sha-<commit>)
    GHA->>EC2: SSH (appleboy/ssh-action)

    EC2->>EC2: ensure docker/compose/appnet
    EC2->>EC2: write .env / mysql my.cnf / nginx conf / compose.yml
    EC2->>DB: compose up -d db
    loop wait up to ~120s
      EC2->>DB: mysqladmin ping (healthcheck)
    end
    EC2->>DB: init DB & user (IF NOT EXISTS)

    EC2->>Web: compose run web migrate (--fake-initial fallback)
    EC2->>Web: apply_socialapp & set Django Site(wisheasy.site)
    EC2->>Web: load_csv (idempotent marker)
    EC2->>Web: collectstatic
    EC2->>Web: build_graph

    EC2->>Nginx: compose up -d web nginx
    Nginx-->>Web: proxy_pass :8000
  end
```

