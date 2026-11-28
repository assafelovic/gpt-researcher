<div align="center" id="top">

<img src="https://raw.githubusercontent.com/assafelovic/gpt-researcher/main/docs/static/img/gptr-logo-tile.png" alt="شعار GPT Researcher" width="80">

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

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md) | [Русский](README-ru_RU.md) | [العربية](README-ar_SA.md)

</div>

<div dir="rtl">

# 🔎 GPT Researcher

**GPT Researcher هو أول وكيل بحث معمّق مفتوح، مصمَّم للبحث على الويب وفي المصادر المحلية معًا، لأي مهمة.**

ينتج الوكيل تقارير بحثية مفصّلة ومبنية على الوقائع وغير منحازة، مع الاستشهادات المرجعية. ويوفّر GPT Researcher مجموعة كاملة من خيارات التخصيص لإنشاء وكلاء بحث مصمَّمين لاحتياجاتك ومتخصصين في مجالات بعينها. ويتجاوز GPT Researcher حدود RAG بكثير: إذ يقسّم وكلاء التخطيط والتنفيذ كل مهمة إلى أسئلة بحثية، وتُبقي [نماذج القرار](#-smart-context-filtering-with-jev) على السياق المفيد فعلًا للإجابة عنها وحده، وتتولّى مسارات العمل [متعددة الوكلاء](#-multi-agent-assistant) التنسيق بين وكلاء متخصصين من التخطيط حتى النشر، ويستكشف [البحث المعمّق التعاودي](#-deep-research) الموضوع اتساعًا وعمقًا. يجري البحث على التوازي، فيبقى سريعًا ومستقرًا وموثوقًا، ويقلّل المعلومات المضلِّلة.

**مهمتنا هي تمكين الأفراد والمؤسسات من الحصول على معلومات دقيقة وغير منحازة ومبنية على الوقائع بفضل الذكاء الاصطناعي.**

## لماذا GPT Researcher؟

- قد يستغرق التوصّل إلى استنتاجات موضوعية عبر البحث اليدوي أسابيع، ويتطلب موارد ووقتًا هائلين.
- قد تهلوس النماذج اللغوية الكبيرة (LLMs) المدرَّبة على معلومات قديمة، فلا تعود صالحة لمهام البحث الحالية.
- للنماذج اللغوية الحالية حدود على عدد الرموز (tokens)، وهي غير كافية لتوليد تقارير بحثية طويلة.
- تؤدي محدودية مصادر الويب في الخدمات القائمة إلى معلومات مضلِّلة ونتائج سطحية.
- قد يُدخل الاختيار الانتقائي لمصادر الويب انحيازًا إلى مهام البحث.

## العرض التوضيحي

</div>

<a href="https://github.com/user-attachments/assets/4d3f26cf-8ccc-413a-b17c-80aa9e1b52d1">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="https://github.com/user-attachments/assets/25d92184-c59e-4115-9961-759ada1ec952">
    <img src="https://github.com/user-attachments/assets/3a56a008-fcbd-4373-9e40-8d6027120cfb" alt="GPT Researcher يحوّل سؤالًا إلى تقرير موثَّق بالمصادر" width="800">
  </picture>
</a>

<div dir="rtl">

## التثبيت بوصفه Claude Skill

وسّع قدرات البحث المعمّق لدى Claude بتثبيت GPT Researcher بوصفه [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher):

</div>

```bash
npx skills add assafelovic/gpt-researcher
```

<div dir="rtl">

بمجرد التثبيت، يستطيع Claude الاستفادة من قدرات البحث المعمّق في GPT Researcher مباشرةً داخل محادثاتك.

## البنية

الفكرة الأساسية هي استخدام وكلاء «المخطِّط» (planner) و«التنفيذ» (execution). يولّد المخطِّط الأسئلة البحثية، بينما يجمع وكلاء التنفيذ المعلومات ذات الصلة. ثم يجمع الناشر (publisher) كل النتائج في تقرير شامل.

</div>

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>

<div dir="rtl">

الخطوات:
* إنشاء وكيل مخصّص للمهمة استنادًا إلى سؤال البحث.
* توليد أسئلة تشكّل معًا رأيًا موضوعيًا في المهمة.
* استخدام وكيل زاحف (crawler) لجمع المعلومات عن كل سؤال.
* تلخيص كل مصدر مع تتبّع مرجعه.
* تصفية الملخصات وتجميعها في تقرير بحثي نهائي.

## الدروس التعليمية
 - [كيف يعمل](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [كيفية التثبيت](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [عرض مباشر](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## المزايا

- 📝 توليد تقارير بحثية مفصّلة باستخدام الويب والمستندات المحلية.
- 🖼️ استخلاص ذكي للصور وتصفيتها من أجل التقارير.
- 🍌 **صور مولَّدة بالذكاء الاصطناعي ومضمّنة في التقرير** باستخدام Google Gemini (Nano Banana) لإضافة رسوم توضيحية.
- 📜 توليد تقارير مفصّلة تتجاوز 2,000 كلمة.
- 🌐 تجميع أكثر من 20 مصدرًا للوصول إلى استنتاجات موضوعية.
- 🎯 تصفية ذكية للسياق باستخدام [Jev](#-smart-context-filtering-with-jev)، دون الحاجة افتراضيًا إلى مفتاح API أو تضمينات (embeddings).
- 🖥️ واجهة أمامية متاحة بنسختين: خفيفة (HTML/CSS/JS) وجاهزة للإنتاج (NextJS + Tailwind).
- 🔍 استخلاص محتوى الويب مع دعم JavaScript.
- 📂 الاحتفاظ بالذاكرة والسياق طوال عملية البحث.
- 📄 تصدير التقارير إلى PDF وWord وصيغ أخرى.
- 💰 نحو 0.08 دولار ودقيقة واحدة لكل تقرير بحثي باستخدام النماذج الافتراضية، مع تتبّع تكلفة كل عملية تشغيل ([تفصيل التكلفة](https://docs.gptr.dev/docs/gpt-researcher/gptr/costs)).

## 📖 التوثيق

راجع [التوثيق](https://docs.gptr.dev/docs/gpt-researcher/getting-started) للاطلاع على:
- أدلة التثبيت والإعداد
- خيارات الضبط والتخصيص
- [التكاليف](https://docs.gptr.dev/docs/gpt-researcher/gptr/costs) لكل نوع من التقارير وكيفية خفضها
- أمثلة «كيف أفعل»
- مراجع API الكاملة

## ⚙️ البدء

### التثبيت

1. ثبّت Python 3.12 أو أحدث. [الدليل](https://www.tutorialsteacher.com/python/install-python).
2. انسخ المشروع (clone) وانتقل إلى المجلد:

</div>

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

<div dir="rtl">

3. اضبط مفاتيح API بتعيينها كمتغيرات بيئة (export) أو بتخزينها في ملف `.env`.

</div>

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
export TAVILY_API_KEY={Your Tavily API Key here}
```

<div dir="rtl">

(اختياري) لتحسين التتبّع والمراقبة، يمكنك أيضًا ضبط:

</div>

```bash
# export LANGCHAIN_TRACING_V2=true
# export LANGCHAIN_API_KEY={Your LangChain API Key here}
```

<div dir="rtl">

لواجهات API المتوافقة مع OpenAI والمخصّصة (مثل النماذج المحلية أو المزوّدين الآخرين)، يمكنك أيضًا ضبط:

</div>

```bash
export OPENAI_BASE_URL={Your custom API base URL here}
```

<div dir="rtl">

4. ثبّت الاعتماديات وشغّل الخادم:

</div>

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

<div dir="rtl">

زُر [http://localhost:8000](http://localhost:8000) للبدء.

لإعدادات أخرى (مثل Poetry أو البيئات الافتراضية)، راجع [صفحة البدء](https://docs.gptr.dev/docs/gpt-researcher/getting-started).

## التشغيل كحزمة PIP

</div>

```bash
pip install gpt-researcher

```

<div dir="rtl">

### مثال على الاستخدام:

</div>

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

<div dir="rtl">

**لمزيد من الأمثلة والإعدادات، يُرجى الرجوع إلى صفحة [توثيق PIP](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package).**

### 🔧 عميل MCP
يدعم GPT Researcher التكامل مع MCP للاتصال بمصادر بيانات متخصصة مثل مستودعات GitHub وقواعد البيانات وواجهات API المخصّصة. وهذا يتيح البحث في مصادر البيانات إلى جانب البحث على الويب.

</div>

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

<div dir="rtl">

> للاطلاع على توثيق MCP الشامل وأمثلة متقدمة، زُر [دليل تكامل MCP](https://docs.gptr.dev/docs/gpt-researcher/retrievers/mcp-configs).

## 🍌 توليد الصور المضمّنة

يستطيع GPT Researcher توليد رسوم توضيحية بالذكاء الاصطناعي وتضمينها تلقائيًا في تقاريره البحثية باستخدام نماذج Gemini من Google (Nano Banana).

</div>

```bash
# Enable in your .env file
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=your_google_api_key
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
```

<div dir="rtl">

عند التفعيل، سيقوم النظام بما يلي:
1. تحليل سياق بحثك لتحديد فرص إضافة عناصر بصرية
2. توليد 2-3 صور ذات صلة مسبقًا أثناء مرحلة البحث
3. تضمينها داخل التقرير أثناء كتابته

تُولَّد الصور بنمط الوضع الداكن المتوافق مع واجهة GPT Researcher، وبجماليات إنفوغرافيك احترافية ولمسات بلون التيل (teal).

[اعرف المزيد عن توليد الصور](https://docs.gptr.dev/docs/gpt-researcher/gptr/image_generation) في توثيقنا.

<a id="-deep-research"></a>

## ✨ البحث المعمّق (Deep Research)

يتضمّن GPT Researcher الآن البحث المعمّق (Deep Research)، وهو سير عمل متقدم تعاودي يستكشف المواضيع بعمق واتساع على طريقة الوكلاء. تعتمد هذه الميزة نمط استكشاف شجري، فتتعمّق في الموضوعات الفرعية مع الحفاظ على رؤية شاملة لموضوع البحث.

- 🌳 استكشاف شجري بعمق واتساع قابلين للضبط
- ⚡️ معالجة متوازية للحصول على نتائج أسرع
- 🤝 إدارة ذكية للسياق عبر فروع البحث
- ⏱️ يستغرق نحو 7–12 دقيقة لكل بحث معمّق
- 💰 تبلغ تكلفته نحو 1.30 دولار لكل بحث معمّق مع النماذج والإعدادات الافتراضية ([تفصيل التكلفة](https://docs.gptr.dev/docs/gpt-researcher/gptr/costs))

[اعرف المزيد عن البحث المعمّق](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research) في توثيقنا.

<a id="-smart-context-filtering-with-jev"></a>

## 🎯 التصفية الذكية للسياق باستخدام Jev

يستخلص كل تشغيل بحثي عشرات الصفحات، ولا يفيد في الإجابة عن السؤال سوى جزء من كل صفحة. وقبل أن يصل أي شيء إلى النموذج اللغوي، يقرّر GPT Researcher أي المقاطع يُبقي عليها. يستخدم افتراضيًا **[Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)** من TypeSafe، وهو نموذج يقيس مدى فائدة كل مقطع للسؤال، بدلًا من قياس تشابه كلماته أو تضمينه (embedding) مع السؤال.

**سياق Jev أكثر صلة بنسبة 59% من التضمينات، وبالتكلفة نفسها** (73% من المقاطع المُبقاة ذات صلة مقابل 46%). أجرينا اختبارًا مقارنًا لكل الخيارات على 28 مهمة بحثية، مع إعادة استخدام المصادر المستخلصة نفسها بحيث يتغيّر المرشِّح وحده:

| مرشِّح السياق | المقاطع ذات الصلة المُبقاة | مقارنة مباشرة مع التضمينات | زمن التصفية | التكلفة لكل تقرير | المتطلبات |
|---|---|---|---|---|---|
| **Jev** (الافتراضي) | **73%** | **15 فوزًا · 10 تعادلات · 3 خسائر** | 1.7 ثانية | 0.115 دولار | `TYPESAFE_API_KEY` |
| الكلمات المفتاحية (احتياطي) | 51% | 14 فوزًا · 8 تعادلات · 6 خسائر | 0.02 ثانية | 0.116 دولار | لا شيء |
| التضمينات | 46% | — | 1.0 ثانية | 0.117 دولار | مزوّد تضمينات |
| بلا تصفية | — | 13 فوزًا · 11 تعادلًا · 4 خسائر | — | 0.192 دولار | لا شيء |

تستغرق كتابة التقرير نحو 45 ثانية أيًّا كان المرشِّح المستخدم، لذا يتغيّر الزمن الإجمالي للتشغيل بمقدار خطوة التصفية وحدها. أما تمرير كل الصفحات دون تصفية فيُنتج أوسع التقارير في الأسئلة المفتوحة، لكنه يكلّف أكثر بنسبة 65%.

**لا شيء مطلوب.** مع وجود `TYPESAFE_API_KEY` يُستخدم Jev. وبدونه، أو إذا فشل استدعاء Jev، يعود GPT Researcher إلى الترتيب بالكلمات المفتاحية (BM25)، وهو يعمل محليًا دون مفتاح API أو نموذج أو تضمينات. وتبقى التضمينات متاحة كخيار.

</div>

```bash
export TYPESAFE_API_KEY=...   # use Jev (the default when a key is set)
export CONTEXT_FILTER=auto    # auto | jev | keyword | embeddings | none
```

<div dir="rtl">

راجع [توثيق مرشِّح السياق](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter) و[المقياس المرجعي الكامل](evals/context_filter) لمعرفة المنهجية والمحاذير وطريقة إعادة إنتاج النتائج.

## التشغيل عبر Docker

> **الخطوة 1** - [ثبّت Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **الخطوة 2** - انسخ الملف '.env.example'، وأضف مفاتيح API الخاصة بك إلى الملف المنسوخ، ثم احفظه باسم '.env'

> **الخطوة 3** - داخل ملف docker-compose، علّق (comment out) الخدمات التي لا تريد تشغيلها عبر Docker.

</div>

```bash
docker-compose up --build
```

<div dir="rtl">

إذا لم يعمل ذلك، فجرّب تشغيله بدون الشرطة:

</div>

```bash
docker compose up --build
```

<div dir="rtl">

> **الخطوة 4** - افتراضيًا، إذا لم تُلغِ التعليق عن أي شيء في ملف docker-compose، فسيشغّل هذا المسار عمليتين:
 - خادم Python الذي يعمل على localhost:8000<br>
 - تطبيق React الذي يعمل على localhost:3000<br>

زُر localhost:3000 في أي متصفح واستمتع بالبحث!


## 📄 البحث في المستندات المحلية

يمكنك توجيه GPT Researcher إلى تنفيذ مهام البحث اعتمادًا على مستنداتك المحلية. صيغ الملفات المدعومة حاليًا هي: PDF والنص العادي وCSV وExcel وMarkdown وPowerPoint ومستندات Word.

الخطوة 1: أضف متغير البيئة `DOC_PATH` الذي يشير إلى المجلد الذي توجد فيه مستنداتك.

</div>

```bash
export DOC_PATH="./my-docs"
```

<div dir="rtl">

الخطوة 2:
 - إذا كنت تشغّل تطبيق الواجهة الأمامية على localhost:8000، فاختر ببساطة "My Documents" من خيارات القائمة المنسدلة "Report Source".
 - إذا كنت تشغّل GPT Researcher عبر [حزمة PIP](https://docs.tavily.com/guides/gpt-researcher/gpt-researcher#pip-package)، فمرّر الوسيط `report_source` بالقيمة "local" عند إنشاء كائن من الفئة `GPTResearcher` [مثال برمجي هنا](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research).


## 🤖 خادم MCP

نقلنا خادم MCP الخاص بنا إلى مستودع مخصّص: [gptr-mcp](https://github.com/assafelovic/gptr-mcp).

يتيح خادم GPT Researcher MCP لتطبيقات الذكاء الاصطناعي مثل Claude إجراء بحث معمّق. وبينما تستطيع تطبيقات النماذج اللغوية الوصول إلى أدوات البحث على الويب عبر MCP، يقدّم GPT Researcher MCP نتائج بحث أعمق وأكثر موثوقية.

المزايا:
- قدرات بحث معمّق لمساعدي الذكاء الاصطناعي
- معلومات أعلى جودة مع استخدام مُحسَّن للسياق
- نتائج شاملة مع استدلال أفضل للنماذج اللغوية
- تكامل مع Claude Desktop

للاطلاع على تعليمات التثبيت والاستخدام التفصيلية، زُر [المستودع الرسمي](https://github.com/assafelovic/gptr-mcp).


<a id="-multi-agent-assistant"></a>

## 👪 المساعد متعدد الوكلاء
مع تطوّر الذكاء الاصطناعي من هندسة الأوامر (prompt engineering) وRAG إلى الأنظمة متعددة الوكلاء، يسعدنا أن نقدّم مساعدين متعددي الوكلاء مبنيين باستخدام [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) و[AG2](https://github.com/ag2ai/ag2).

باستخدام أطر العمل متعددة الوكلاء، يمكن تحسين عملية البحث تحسينًا كبيرًا من حيث العمق والجودة عبر الاستفادة من عدة وكلاء يملكون مهارات متخصصة. يعرض هذا المشروع كيف يستطيع فريق من وكلاء الذكاء الاصطناعي العمل معًا لإجراء بحث في موضوع معيّن، من التخطيط حتى النشر.

ينتج التشغيل المتوسط تقريرًا بحثيًا من 5 إلى 6 صفحات بصيغ متعددة مثل PDF وDocx وMarkdown.

اطّلع عليه [هنا](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents) أو انتقل إلى توثيقنا الخاص بـ[LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) و[AG2](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2) لمزيد من المعلومات.

## 🔍 المراقبة (Observability)

يدعم GPT Researcher أداة **LangSmith** لتحسين التتبّع والمراقبة، مما يسهّل تصحيح أخطاء سير العمل المعقدة متعددة الوكلاء وتحسينها.

لتفعيل التتبّع:
1. اضبط متغيرات البيئة التالية:

</div>

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_api_key
export LANGCHAIN_PROJECT="gpt-researcher"
```

<div dir="rtl">

2. شغّل مهام البحث كالمعتاد. ستُتتبَّع جميع تفاعلات الوكلاء المبنية على LangGraph وتُعرض تلقائيًا في لوحة LangSmith الخاصة بك.

## 🖥️ تطبيقات الواجهة الأمامية

يتضمّن GPT-Researcher الآن واجهة أمامية مطوَّرة لتحسين تجربة المستخدم وتبسيط عملية البحث. توفّر الواجهة الأمامية ما يلي:

- واجهة بديهية لإدخال استعلامات البحث
- تتبّع فوري لتقدّم مهام البحث
- عرض تفاعلي لنتائج البحث
- إعدادات قابلة للتخصيص لتجارب بحث تناسب احتياجاتك

يتوفر خياران للنشر:
1. واجهة أمامية ثابتة خفيفة تقدّمها FastAPI
2. تطبيق NextJS غني بالمزايا للوظائف المتقدمة

للاطلاع على تعليمات الإعداد التفصيلية ومزيد من المعلومات عن مزايا الواجهة الأمامية، زُر [صفحة التوثيق](https://docs.gptr.dev/docs/gpt-researcher/frontend/introduction).

## 🚀 المساهمة
نرحّب بالمساهمات بشدة! يُرجى الاطلاع على [دليل المساهمة](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md) إذا كنت مهتمًا.

اطّلع على صفحة [خارطة الطريق](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) وتواصل معنا عبر [مجتمع Discord](https://discord.gg/QgZXvJAccX) إذا كنت ترغب في الانضمام إلى مهمتنا.
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher&max=1000" />
</a>
## ✉️ الدعم / تواصل معنا
- [مجتمع Discord](https://discord.gg/spBgZmm3Xe)
- البريد الإلكتروني للمؤلف: assaf.elovic@gmail.com

## 🛡 إخلاء المسؤولية

هذا المشروع، GPT Researcher، تطبيق تجريبي ويُقدَّم «كما هو» دون أي ضمان، صريحًا كان أم ضمنيًا. نشارك الشيفرة البرمجية لأغراض أكاديمية بموجب رخصة Apache 2. لا يُعدّ شيء مما ورد هنا نصيحة أكاديمية، ولا يُعدّ توصيةً باستخدام هذا المشروع في الأوراق الأكاديمية أو البحثية.

موقفنا من ادعاءات البحث غير المنحاز:
1. الهدف الرئيسي لـ GPT Researcher هو تقليل الحقائق الخاطئة والمنحازة. كيف؟ نفترض أنه كلما زاد عدد المواقع التي نستخلص منها المحتوى قلّ احتمال وجود بيانات خاطئة. فباستخلاص المحتوى من مواقع متعددة في كل بحث، واختيار المعلومات الأكثر تكرارًا، يصبح احتمال أن تكون جميعها خاطئة ضئيلًا للغاية.
2. لا نهدف إلى القضاء على التحيّز، بل إلى تقليله قدر الإمكان. **نحن هنا كمجتمع لنكتشف أنجع أشكال التفاعل بين الإنسان والنماذج اللغوية الكبيرة.**
3. في البحث، يميل الناس أيضًا إلى التحيّز، إذ إن لدى معظمهم آراءً مسبقة في المواضيع التي يبحثون فيها. تستخلص هذه الأداة آراءً كثيرة وتشرح بإنصاف وجهات نظر متنوعة لم يكن الشخص المنحاز ليقرأها أبدًا.

</div>

---

<p align="center">
<a href="https://star-history.com/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="مخطط تاريخ النجوم" src="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>


<p align="right">
  <a href="#top">⬆️ العودة إلى الأعلى</a>
</p>

ترجمة: فريق مُشَيِّد
