<div align="center">
<!--<h1 style="display: flex; align-items: center; gap: 10px;">
  <img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/a45bac7c-092c-42e5-8eb6-69acbf20dde5" alt="Logo" width="25">
  GPT Researcher
</h1>-->
<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">


####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord Follow](https://img.shields.io/discord/1127851779011391548?style=for-the-badge&logo=discord&label=Chat%20on%20Discord)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) |
[中文](README-zh_CN.md) |
[日本語](README-ja_JP.md) |
[한국어](README-ko_KR.md)
</div>

# 🔎 GPT Researcher

**GPT Researcher는 다양한 작업을 대해 포괄적인 온라인 연구를 수행하도록 설계된 자율 에이전트입니다.**

이 에이전트는 세부적이고 사실에 기반하며 편견 없는 연구 보고서를 생성할 수 있으며, 관련 리소스와 개요에 초점을 맞춘 맞춤형 옵션을 제공합니다.  최근 발표된 [Plan-and-Solve](https://arxiv.org/abs/2305.04091) 및 [RAG](https://arxiv.org/abs/2005.11401) 논문에서 영감을 받아 GPT Researcher는 잘못된 정보, 속도, 결정론적 접근 방식, 신뢰성 문제를 해결하고, 동기화 작업이 아닌 병렬 에이전트 작업을 통해 더 안정적이고 빠른 성능을 제공합니다.

**우리의 목표는 AI의 힘을 활용하여 개인과 조직에게 정확하고 편향 없는 사실에 기반한 정보를 제공하는 것입니다.**

## 왜 GPT Researcher인가?

- 직접 수행하는 연구 과정은 객관적인 결론을 도출하는 데 시간이 오래 걸리며, 적절한 리소스와 정보를 찾는 데 몇 주가 걸릴 수 있습니다.
- 현재의 대규모 언어 모델(LLM)은 과거 정보에 기반해 훈련되었으며, 환각 현상이 발생할 위험이 높아 연구 작업에는 적합하지 않습니다.
- 현재 LLM은 짧은 토큰 출력으로 제한되며, 2,000단어 이상의 길고 자세한 연구 보고서를 작성하는 데는 충분하지 않습니다.
- 웹 검색을 지원하는 서비스(예: ChatGPT 또는 Perplexity)는 제한된 리소스와 콘텐츠만을 고려하여 경우에 따라 피상적이고 편향된 답변을 제공합니다.
- 웹 소스만을 사용하면 연구 작업에서 올바른 결론을 도출할 때 편향이 발생할 수 있습니다.

## 데모
https://github.com/user-attachments/assets/092e9e71-7e27-475d-8c4f-9dddd28934a3

## 아키텍처
주요 아이디어는 "플래너"와 "실행" 에이전트를 실행하는 것으로, 플래너는 연구할 질문을 생성하고, 실행 에이전트는 생성된 각 연구 질문에 따라 가장 관련성 높은 정보를 찾습니다. 마지막으로 플래너는 모든 관련 정보를 필터링하고 집계하여 연구 보고서를 작성합니다.
<br /> <br /> 
에이전트는 `gpt-4o-mini`와 `gpt-4o`(128K 컨텍스트)를 활용하여 연구 작업을 완료합니다. 필요에 따라 각각을 사용하여 비용을 최적화합니다. **평균 연구 작업은 약 2분이 소요되며, 비용은 약 $0.005입니다.**.

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>

구체적으로:
* 연구 쿼리 또는 작업을 기반으로 도메인별 에이전트를 생성합니다.
* 주어진 작업에 대해 객관적인 의견을 형성할 수 있는 일련의 연구 질문을 생성합니다.
* 각 연구 질문에 대해 크롤러 에이전트를 실행하여 작업과 관련된 정보를 온라인 리소스에서 수집합니다.
* 수집된 각 리소스에서 관련 정보를 요약하고 출처를 기록합니다.
* 마지막으로, 요약된 모든 정보를 필터링하고 집계하여 최종 연구 보고서를 생성합니다.

## 튜토리얼
 - [동작원리](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [설치방법](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [라이브 데모](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)


## 기능
- 📝 로컬 문서 및 웹 소스를 사용하여 연구, 개요, 리소스 및 학습 보고서 생성
- 📜 2,000단어 이상의 길고 상세한 연구 보고서 생성 가능
- 🌐 연구당 20개 이상의 웹 소스를 집계하여 객관적이고 사실에 기반한 결론 도출
- 🖥️ 경량 HTML/CSS/JS와 프로덕션용 (NextJS + Tailwind) UX/UI 포함
- 🔍 자바스크립트 지원 웹 소스 스크래핑 기능
- 📂 연구 과정에서 맥락과 메모리 추적 및 유지
- 📄 연구 보고서를 PDF, Word 등으로 내보내기 지원

## 📖 문서

전체 문서(설치, 환경 설정, 간단한 예시)를 보려면 [여기](https://docs.gptr.dev/docs/gpt-researcher/getting-started)를 참조하세요.

- 시작하기 (설치, 환경 설정, 간단한 예시)
- 맞춤 설정 및 구성
- 사용 방법 예시 (데모, 통합, 도커 지원)
- 참고자료 (전체 API 문서)

## ⚙️ 시작하기
### 설치
> **1단계** - Python 3.11 또는 그 이상의 버전을 설치하세요. [여기](https://www.tutorialsteacher.com/python/install-python)를 참조하여 단계별 가이드를 확인하세요.

> **2단계** - 프로젝트를 다운로드하고 해당 디렉토리로 이동하세요.

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

> **3단계** - 두 가지 방법으로 API 키를 설정하세요: 직접 export하거나 `.env` 파일에 저장하세요.

Linux/Windows에서 임시 설정을 하려면 export 방법을 사용하세요:

```bash
export OPENAI_API_KEY={OpenAI API 키 입력}
export TAVILY_API_KEY={Tavily API 키 입력}
```

더 영구적인 설정을 원한다면, 현재의 `gpt-researcher` 디렉토리에 `.env` 파일을 생성하고 환경 변수를 입력하세요 (export 없이).

- 기본 LLM은 [GPT](https://platform.openai.com/docs/guides/gpt)이지만, `claude`, `ollama3`, `gemini`, `mistral` 등 다른 LLM도 사용할 수 있습니다. LLM 제공자를 변경하는 방법은 [LLMs 문서](https://docs.gptr.dev/docs/gpt-researcher/llms)를 참조하세요. 이 프로젝트는 OpenAI GPT 모델에 최적화되어 있습니다.
- 기본 검색기는 [Tavily](https://app.tavily.com)이지만, `duckduckgo`, `google`, `bing`, `searchapi`, `serper`, `searx`, `arxiv`, `exa` 등의 검색기를 사용할 수 있습니다. 검색 제공자를 변경하는 방법은 [검색기 문서](https://docs.gptr.dev/docs/gpt-researcher/retrievers)를 참조하세요.

### 빠른 시작

> **1단계** - 필요한 종속성 설치

```bash
pip install -r requirements.txt
```

> **2단계** - FastAPI로 에이전트 실행

```bash
python -m uvicorn main:app --reload
```

> **3단계** - 브라우저에서 http://localhost:8000 으로 이동하여 연구를 시작하세요!

<br />

**[Poetry](https://docs.gptr.dev/docs/gpt-researcher/getting-started#poetry) 또는 [가상 환경](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started#virtual-environment)에 대해 배우고 싶다면, [문서](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started)를 참조하세요.**

### PIP 패키지로 실행하기
```bash
pip install gpt-researcher
```

```python
...
from gpt_researcher import GPTResearcher

query = "왜 Nvidia 주식이 오르고 있나요?"
researcher = GPTResearcher(query=query, report_type="research_report")
# 주어진 질문에 대한 연구 수행
research_result = await researcher.conduct_research()
# 보고서 작성
report = await researcher.write_report()
...
```

**더 많은 예제와 구성 옵션은 [PIP 문서](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)를 참조하세요.**

## Docker로 실행

> **1단계** - [Docker 설치](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **2단계** - `.env.example` 파일을 복사하고 API 키를 추가한 후, 파일을 `.env`로 저장하세요.

> **3단계** - docker-compose 파일에서 실행하고 싶지 않은 서비스를 주석 처리하세요.

```bash
$ docker-compose up --build
```

> **4단계** - docker-compose 파일에서 아무 것도 주석 처리하지 않았다면, 기본적으로 두 가지 프로세스가 시작됩니다:
 - localhost:8000에서 실행 중인 Python 서버<br>
 - localhost:3000에서 실행 중인 React 앱<br>

브라우저에서 localhost:3000으로 이동하여 연구를 시작하세요!

## 📄 로컬 문서로 연구하기

GPT Researcher를 사용하여 로컬 문서를 기반으로 연구 작업을 수행할 수 있습니다. 현재 지원되는 파일 형식은 PDF, 일반 텍스트, CSV, Excel, Markdown, PowerPoint, Word 문서입니다.

1단계: `DOC_PATH` 환경 변수를 설정하여 문서가 있는 폴더를 지정하세요.

```bash
export DOC_PATH="./my-docs"
```

2단계:
 - 프론트엔드 앱을 localhost:8000에서 실행 중이라면, "Report Source" 드롭다운 옵션에서 "My Documents"를 선택하세요.
 - GPT Researcher를 [PIP 패키지](https://docs.tavily.com/guides/gpt-researcher/gpt-researcher#pip-package)로 실행 중이라면, `report_source` 인수를 "local"로 설정하여 `GPTResearcher` 클래스를 인스턴스화하세요. [코드 예제](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research)를 참조하세요.

## 👪 다중 에이전트 어시스턴트

AI가 프롬프트 엔지니어링 및 RAG에서 다중 에이전트 시스템으로 발전함에 따라, 우리는 [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/)로 구축된 새로운 다중 에이전트 어시스턴트를 소개합니다.

LangGraph를 사용하면 여러 에이전트의 전문 기술을 활용하여 연구 과정의 깊이와 질을 크게 향상시킬 수 있습니다. 최근 [STORM](https://arxiv.org/abs/2402.14207) 논문에서 영감을 받아, 이 프로젝트는 AI 에이전트 팀이 주제에 대한 연구를 계획에서 출판까지 함께 수행하는 방법을 보여줍니다.

평균 실행은 5-6 페이지 분량의 연구 보고서를 PDF, Docx, Markdown 형식으로 생성합니다.

[여기](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents)에서 확인하거나 [문서](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)에서 자세한 내용을 참조하세요.

## 🖥️ 프론트엔드 애플리케이션

GPT-Researcher는 사용자 경험을 개선하고 연구 프로세스를 간소화하기 위해 향상된 프론트엔드를 제공합니다. 프론트엔드는 다음과 같은 기능을 제공합니다:

- 연구 쿼리를 입력할 수 있는 직관적인 인터페이스
- 연구 작업의 실시간 진행 상황 추적
- 연구 결과의 대화형 디스플레이
- 맞춤형 연구 경험을 위한 설정 가능

두 가지 배포 옵션이 있습니다:
1. FastAPI로 제공되는 경량 정적 프론트엔드
2. 고급 기능을 제공하는 NextJS 애플리케이션

프론트엔드 기능에 대한 자세한 설치 방법 및 정보를 원하시면 [문서 페이지](https://docs.gptr.dev/docs/gpt-researcher/frontend/introduction)를 참조하세요.

## 🚀 기여하기
우리는 기여를 적극 환영합니다! 관심이 있다면 [기여 가이드](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md)를 확인해 주세요.

[로드맵](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) 페이지를 확인하고, 우리 [Discord 커뮤니티](https://discord.gg/QgZXvJAccX)에 가입하여 우리의 목표에 함께 참여해 주세요.
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher" />
</a>

## ✉️ 지원 / 문의
- [커뮤니티 Discord](https://discord.gg/spBgZmm3Xe)
- 저자 이메일: assaf.elovic@gmail.com

## 🛡️ 면책 조항

이 프로젝트인 GPT Researcher는 실험적인 응용 프로그램이며, 명시적이거나 묵시적인 보증 없이 "있는 그대로" 제공됩니다. 우리는 이 코드를 학술적 목적으로 Apache 2 라이선스 하에 공유하고 있습니다. 여기에 있는 것은 학술적 조언이 아니며, 학술 또는 연구 논문에 사용하는 것을 권장하지 않습니다.

편향되지 않은 연구 주장에 대한 우리의 견해:
1. GPT Researcher의 주요 목표는 잘못된 정보와 편향된 사실을 줄이는 것입니다. 그 방법은 무엇일까요? 우리는 더 많은 사이트를 스크래핑할수록 잘못된 데이터의 가능성이 줄어든다고 가정합니다. 여러 사이트에서 정보를 스크래핑하고 가장 빈번한 정보를 선택하면, 모든 정보가 틀릴 확률은 매우 낮습니다.
2. 우리는 편향을 완전히 제거하려고 하지는 않지만, 가능한 한 줄이는 것을 목표로 합니다. **우리는 인간과 LLM의 가장 효과적인 상호작용을 찾기 위한 커뮤니티입니다.**
3. 연구에서 사람들도 이미 자신이 연구하는 주제에 대해 의견을 가지고 있기 때문에 편향되는 경향이 있습니다. 이 도구는 많은 의견을 스크래핑하며, 편향된 사람이라면 결코 읽지 않았을 다양한 견해를 고르게 설명합니다.

**GPT-4 모델을 사용할 경우, 토큰 사용량 때문에 비용이 많이 들 수 있습니다.** 이 프로젝트를 사용하는 경우, 자신의 토큰 사용량 및 관련 비용을 모니터링하고 관리하는 것은 본인의 책임입니다. OpenAI API 사용량을 정기적으로 확인하고, 예상치 못한 비용을 방지하기 위해 필요한 한도를 설정하거나 알림을 설정하는 것이 좋습니다.


---

<p align="center">
<a href="https://star-history.com/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>
