<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord](https://img.shields.io/discord/1127851779011391548?logo=discord&logoColor=white&label=Discord&color=34b76a&style=for-the-badge)](https://discord.gg/QgZXvJAccX)


[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Skill](https://img.shields.io/badge/Claude%20Skill-skills.sh-blueviolet?style=flat&logo=anthropic&logoColor=white)](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md) | [Русский](README-ru_RU.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher — первый открытый агент глубокого исследования, рассчитанный и на веб, и на локальные источники по любой задаче.**

Агент готовит подробные, фактические и непредвзятые исследовательские отчёты со ссылками. GPT Researcher даёт полный набор настроек, чтобы собирать специализированных агентов под конкретную предметную область. Вдохновлённый работами [Plan-and-Solve](https://arxiv.org/abs/2305.04091) и [RAG](https://arxiv.org/abs/2005.11401), проект снижает дезинформацию и повышает скорость, детерминизм и надёжность за счёт стабильной работы и параллелизации агентов.

**Наша миссия — дать людям и организациям точную, непредвзятую и фактическую информацию с помощью ИИ.**

## Зачем GPT Researcher?

- Объективные выводы при ручном исследовании могут занимать недели и требовать огромных ресурсов.
- LLM, обученные на устаревших данных, галлюцинируют и плохо подходят для актуальных исследовательских задач.
- У современных LLM есть лимиты токенов, которых недостаточно для длинных отчётов.
- Мало веб-источников в существующих сервисах ведёт к дезинформации и поверхностным результатам.
- Выборочные источники могут вносить предвзятость в исследование.

## Демо
<a href="https://www.youtube.com/watch?v=f60rlc_QCxE" target="_blank" rel="noopener">
  <img src="https://github.com/user-attachments/assets/ac2ec55f-b487-4b3f-ae6f-b8743ad296e4" alt="Demo video" width="800" target="_blank" />
</a>

## Установка как Claude Skill

Расширьте возможности глубокого исследования Claude, установив GPT Researcher как [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher):

```bash
npx skills add assafelovic/gpt-researcher
```

После установки Claude сможет использовать глубокое исследование GPT Researcher прямо в ваших диалогах.

## Архитектура

Ключевая идея — «планировщик» и «исполнители». Планировщик формирует исследовательские вопросы, исполнители собирают релевантную информацию, а публикатор сводит всё в итоговый отчёт.

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>

Шаги:
* Создать агента под конкретную исследовательскую задачу.
* Сгенерировать вопросы, которые вместе дают объективную картину.
* Для каждого вопроса запустить crawler-агента и собрать информацию.
* Суммировать каждый источник и сохранить ссылки.
* Отфильтровать и агрегировать саммари в финальный отчёт.

## Туториалы
 - [Как это работает](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [Как установить](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Живое демо](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## Возможности

- 📝 Подробные исследовательские отчёты по вебу и локальным документам.
- 🖼️ Умный сбор и фильтрация изображений для отчётов.
- 🍌 **Встроенные ИИ-иллюстрации** через Google Gemini (Nano Banana).
- 📜 Отчёты объёмом более 2000 слов.
- 🌐 Агрегация более 20 источников для объективных выводов.
- 🖥️ Фронтенд: лёгкий (HTML/CSS/JS) и продакшен-вариант (NextJS + Tailwind).
- 🔍 Веб-скрейпинг с поддержкой JavaScript.
- 📂 Память и контекст на протяжении всего исследования.
- 📄 Экспорт в PDF, Word и другие форматы.

## 📖 Документация

См. [документацию](https://docs.gptr.dev/docs/gpt-researcher/getting-started):
- Установка и настройка
- Конфигурация и кастомизация
- How-To примеры
- Полные API-справочники

## ⚙️ Начало работы

### Установка

1. Установите Python 3.11 или новее. [Гайд](https://www.tutorialsteacher.com/python/install-python).
2. Клонируйте проект и перейдите в каталог:

    ```bash
    git clone https://github.com/assafelovic/gpt-researcher.git
    cd gpt-researcher
    ```

3. Задайте API-ключи через `export` или файл `.env`.

    ```bash
    export OPENAI_API_KEY={Your OpenAI API Key here}
    export TAVILY_API_KEY={Your Tavily API Key here}
    ```

    (Необязательно) Для трассировки и наблюдаемости:

    ```bash
    # export LANGCHAIN_TRACING_V2=true
    # export LANGCHAIN_API_KEY={Your LangChain API Key here}
    ```

    Для кастомных OpenAI-совместимых API (локальные модели и другие провайдеры):

    ```bash
    export OPENAI_BASE_URL={Your custom API base URL here}
    ```

4. Установите зависимости и запустите сервер:

    ```bash
    pip install -r requirements.txt
    python -m uvicorn main:app --reload
    ```

Откройте [http://localhost:8000](http://localhost:8000).

Другие варианты (Poetry, виртуальные окружения) — на странице [Getting Started](https://docs.gptr.dev/docs/gpt-researcher/getting-started).

## Запуск как PIP-пакет
```bash
pip install gpt-researcher

```
### Пример:
```python
...
from gpt_researcher import GPTResearcher

query = "why is Nvidia stock going up?"
researcher = GPTResearcher(query=query)
# Conduct research on the given query
research_result = await researcher.conduct_research()
# Write the report
report = await researcher.write_report()
...
```

**Больше примеров и настроек — в [документации PIP](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package).**

### 🔧 MCP-клиент
GPT Researcher поддерживает MCP, чтобы подключать специализированные источники: репозитории GitHub, базы данных и кастомные API. Это позволяет исследовать данные вместе с веб-поиском.

```bash
export RETRIEVER=tavily,mcp  # Enable hybrid web + MCP research
```

```python
from gpt_researcher import GPTResearcher
import asyncio
import os

async def mcp_research_example():
    # Enable MCP with web search
    os.environ["RETRIEVER"] = "tavily,mcp"

    researcher = GPTResearcher(
        query="What are the top open source web research agents?",
        mcp_configs=[
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
            }
        ]
    )

    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report
```

> Полная документация MCP и продвинутые примеры: [MCP Integration Guide](https://docs.gptr.dev/docs/gpt-researcher/retrievers/mcp-configs).

## 🍌 Генерация встроенных изображений

GPT Researcher может автоматически генерировать и вставлять ИИ-иллюстрации в отчёты с помощью моделей Google Gemini (Nano Banana).

```bash
# Enable in your .env file
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=your_google_api_key
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
```

Если включено, система:
1. Анализирует контекст исследования и ищет места для визуализаций
2. Заранее генерирует 2–3 релевантных изображения на этапе исследования
3. Встраивает их в текст по мере написания отчёта

Изображения оформлены в тёмной теме под UI GPT Researcher: инфографика с бирюзовыми акцентами.

[Подробнее о генерации изображений](https://docs.gptr.dev/docs/gpt-researcher/gptr/image_generation) в документации.

## ✨ Deep Research

В GPT Researcher есть Deep Research — рекурсивный исследовательский процесс с агентной глубиной и шириной. Тема исследуется деревом подтем, при этом сохраняется общая картина предмета.

- 🌳 Древовидный обход с настраиваемой глубиной и шириной
- ⚡️ Параллельная обработка для ускорения
- 🤝 Умное управление контекстом между ветвями
- ⏱️ Около 5 минут на одно глубокое исследование
- 💰 Около $0.4 за исследование (модель `o3-mini` с уровнем reasoning `"high"`)

[Подробнее о Deep Research](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research) в документации.

## Запуск в Docker

> **Шаг 1** — [Установите Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Шаг 2** — Скопируйте `.env.example`, добавьте API-ключи и сохраните как `.env`

> **Шаг 3** — В docker-compose закомментируйте сервисы, которые не нужны.

```bash
docker-compose up --build
```

Если не сработает, попробуйте без дефиса:
```bash
docker compose up --build
```

> **Шаг 4** — По умолчанию (если ничего не раскомментировали) запускаются 2 процесса:
 - Python-сервер на localhost:8000<br>
 - React-приложение на localhost:3000<br>

Откройте localhost:3000 в браузере и исследуйте.


## 📄 Исследование локальных документов

GPT Researcher можно направить на ваши локальные документы. Сейчас поддерживаются: PDF, обычный текст, CSV, Excel, Markdown, PowerPoint и Word.

Шаг 1: задайте переменную окружения `DOC_PATH` на папку с документами.

```bash
export DOC_PATH="./my-docs"
```

Шаг 2:
 - Если фронтенд на localhost:8000, выберите "My Documents" в выпадающем списке "Report Source".
 - Если используете [PIP-пакет](https://docs.tavily.com/guides/gpt-researcher/gpt-researcher#pip-package), передайте `report_source="local"` при создании `GPTResearcher` ([пример кода](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research)).


## 🤖 MCP-сервер

MCP-сервер вынесен в отдельный репозиторий: [gptr-mcp](https://github.com/assafelovic/gptr-mcp).

GPT Researcher MCP Server позволяет ИИ-приложениям вроде Claude проводить глубокое исследование. LLM-приложения могут ходить в веб через MCP, но GPT Researcher MCP даёт более глубокие и надёжные результаты.

Возможности:
- Глубокое исследование для ИИ-ассистентов
- Более качественная информация при оптимизированном использовании контекста
- Полные результаты с лучшим рассуждением для LLM
- Интеграция с Claude Desktop

Установка и использование — в [официальном репозитории](https://github.com/assafelovic/gptr-mcp).


## 👪 Мультиагентный ассистент
По мере эволюции ИИ от промпт-инжиниринга и RAG к мультиагентным системам мы представляем ассистентов на [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) и [AG2](https://github.com/ag2ai/ag2).

Мультиагентные фреймворки повышают глубину и качество исследования за счёт агентов с разными навыками. В духе статьи [STORM](https://arxiv.org/abs/2402.14207) команда ИИ-агентов совместно ведёт исследование: от планирования до публикации.

Средний запуск даёт отчёт на 5–6 страниц в PDF, Docx и Markdown.

Смотрите [код](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents) или документацию по [LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) и [AG2](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2).

## 🔍 Наблюдаемость

GPT Researcher поддерживает **LangSmith** для трассировки и наблюдаемости — так проще отлаживать и оптимизировать сложные мультиагентные сценарии.

Чтобы включить трассировку:
1. Задайте переменные окружения:
   ```bash
   export LANGCHAIN_TRACING_V2=true
   export LANGCHAIN_API_KEY=your_api_key
   export LANGCHAIN_PROJECT="gpt-researcher"
   ```
2. Запускайте исследования как обычно. Все взаимодействия агентов на LangGraph будут трассироваться и отображаться в дашборде LangSmith.

#### Трассировка Monocle

GPT Researcher также поддерживает [Monocle](https://github.com/monocle2ai/monocle) — OpenTelemetry-трейсер для агентных приложений. Он записывает весь прогон: вызовы LLM, шаги агентов и инструменты, вместе со входами, выходами, таймингами и числом токенов.

Monocle — опциональный extra и по умолчанию выключен. Установите его и добавьте в `.env`:

```bash
pip install "gpt-researcher[monocle]"
```

```bash
MONOCLE_TRACING=true
MONOCLE_EXPORTERS=file          # file, console, okahu, s3, blob, gcs (default: file)
OKAHU_API_KEY=okh_xxxxxxxx      # required only for the `okahu` exporter
```

Каждый прогон пишет один файл трейса в `.monocle/`; откройте его в [расширении Monocle для VS Code](https://marketplace.visualstudio.com/items?itemName=OkahuAI.monocle-apptrace). Для анализа трейсов между запусками подключите [Okahu](https://www.okahu.ai) (экспортёр `okahu`).

## 🖥️ Фронтенд-приложения

У GPT Researcher обновлённый фронтенд для удобства и более гладкого исследовательского процесса:

- Интуитивный ввод исследовательских запросов
- Отслеживание прогресса в реальном времени
- Интерактивный просмотр результатов
- Настраиваемые параметры под свои сценарии

Два варианта развёртывания:
1. Лёгкий статический фронтенд, который отдаёт FastAPI
2. Функциональное NextJS-приложение

Подробности — на [странице документации](https://docs.gptr.dev/docs/gpt-researcher/frontend/introduction).

## 🚀 Участие
Мы очень рады вкладу! Если интересно — см. [contributing](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md).

Посмотрите [roadmap](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) и напишите нам в [Discord](https://discord.gg/QgZXvJAccX), если хотите присоединиться к миссии.
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher&max=1000" />
</a>
## ✉️ Поддержка / контакты
- [Community Discord](https://discord.gg/spBgZmm3Xe)
- Email автора: assaf.elovic@gmail.com

## 🛡 Отказ от ответственности

Этот проект, GPT Researcher, — экспериментальное приложение и предоставляется «как есть», без каких-либо гарантий, явных или подразумеваемых. Код публикуется в академических целях по лицензии Apache 2. Это не академический совет и НЕ рекомендация использовать инструмент в научных статьях.

Наш взгляд на «непредвзятость» исследований:
1. Главная цель GPT Researcher — снизить число неверных и предвзятых фактов. Как? Чем больше сайтов мы обходим, тем меньше шанс ошибочных данных. Собирая много источников и выбирая наиболее частую информацию, вероятность, что все они ошибочны, крайне мала.
2. Мы не стремимся полностью устранить предвзятость — мы стремимся максимально её снизить. **Мы сообщество, которое ищет самые эффективные взаимодействия человека и LLM.**
3. В исследованиях люди тоже склонны к предвзятости: у большинства уже есть мнение по теме. Этот инструмент собирает много точек зрения и ровно излагает разные взгляды, которые предвзятый человек мог бы никогда не прочитать.

---

<p align="center">
<a href="https://star-history.dera.page/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://star-history.dera.page/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://star-history.dera.page/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="Star History Chart" src="https://star-history.dera.page/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>


<p align="right">
  <a href="#top">⬆️ Наверх</a>
</p>
