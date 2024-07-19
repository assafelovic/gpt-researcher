# 🔎 GPT Researcher
[![公式サイト](https://img.shields.io/badge/公式サイト-gptr.dev-blue?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord フォロー](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge)](https://discord.gg/QgZXvJAccX)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter フォロー](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)
[![PyPI バージョン](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)

-  [English](README.md)
-  [中文](README-zh_CN.md)
-  [日本語](README-ja_JP.md)

**GPT Researcher は、さまざまなタスクに対する包括的なオンラインリサーチのために設計された自律エージェントです。**

このエージェントは、詳細で事実に基づいた偏りのない研究レポートを生成することができ、関連するリソース、アウトライン、およびレッスンに焦点を当てるためのカスタマイズオプションを提供します。最近の [Plan-and-Solve](https://arxiv.org/abs/2305.04091) および [RAG](https://arxiv.org/abs/2005.11401) 論文に触発され、GPT Researcher は速度、決定論、および信頼性の問題に対処し、同期操作ではなく並列化されたエージェント作業を通じてより安定したパフォーマンスと高速化を提供します。

**私たちの使命は、AIの力を活用して、個人や組織に正確で偏りのない事実に基づいた情報を提供することです。**

## なぜGPT Researcherなのか？

- 手動の研究タスクで客観的な結論を形成するには時間がかかることがあり、適切なリソースと情報を見つけるのに数週間かかることもあります。
- 現在のLLMは過去の情報に基づいて訓練されており、幻覚のリスクが高く、研究タスクにはほとんど役に立ちません。
- 現在のLLMは短いトークン出力に制限されており、長く詳細な研究レポート（2,000語以上）には不十分です。
- Web検索を可能にするサービス（ChatGPT + Webプラグインなど）は、限られたリソースとコンテンツのみを考慮し、場合によっては表面的で偏った回答をもたらします。
- Webソースの選択のみを使用すると、研究タスクの正しい結論を導く際にバイアスが生じる可能性があります。

## アーキテクチャ
主なアイデアは、「プランナー」と「実行」エージェントを実行することであり、プランナーは研究する質問を生成し、実行エージェントは生成された各研究質問に基づいて最も関連性の高い情報を探します。最後に、プランナーはすべての関連情報をフィルタリングおよび集約し、研究レポートを作成します。<br /> <br /> 
エージェントは、研究タスクを完了するために gpt3.5-turbo と gpt-4o（128K コンテキスト）の両方を活用します。必要に応じてそれぞれを使用することでコストを最適化します。**平均的な研究タスクは完了するのに約3分かかり、コストは約0.1ドルです**。

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/architecture.png">
</div>


詳細説明:
* 研究クエリまたはタスクに基づいて特定のドメインエージェントを作成します。
* 研究タスクに対する客観的な意見を形成する一連の研究質問を生成します。
* 各研究質問に対して、与えられたタスクに関連する情報をオンラインリソースから収集するクローラーエージェントをトリガーします。
* 各収集されたリソースについて、関連情報に基づいて要約し、そのソースを追跡します。
* 最後に、すべての要約されたソースをフィルタリングおよび集約し、最終的な研究レポートを生成します。

## デモ
https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda

## チュートリアル
 - [動作原理](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [インストール方法](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [ライブデモ](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## 特徴
- 📝 研究、アウトライン、リソース、レッスンレポートを生成
- 🌐 各研究で20以上のWebソースを集約し、客観的で事実に基づいた結論を形成
- 🖥️ 使いやすいWebインターフェース（HTML/CSS/JS）を含む
- 🔍 JavaScriptサポート付きのWebソースをスクレイピング
- 📂 訪問および使用されたWebソースのコンテキストを追跡
- 📄 研究レポートをPDF、Wordなどにエクスポート

## 📖 ドキュメント

完全なドキュメントについては、[こちら](https://docs.gptr.dev/docs/gpt-researcher/getting-started)を参照してください：

- 入門（インストール、環境設定、簡単な例）
- 操作例（デモ、統合、dockerサポート）
- 参考資料（API完全ドキュメント）
- Tavilyアプリケーションインターフェースの統合（コア概念の高度な説明）

## クイックスタート
> **ステップ 0** - Python 3.11 以降をインストールします。[こちら](https://www.tutorialsteacher.com/python/install-python)を参照して、ステップバイステップのガイドを確認してください。

<br />

> **ステップ 1** - プロジェクトをダウンロードします

```bash
$ git clone https://github.com/assafelovic/gpt-researcher.git
$ cd gpt-researcher
```

<br />

> **ステップ2** - 依存関係をインストールします
```bash
$ pip install -r requirements.txt
```
<br />

> **ステップ 3** - OpenAI キーと Tavily API キーを使用して .env ファイルを作成するか、直接エクスポートします

```bash
$ export OPENAI_API_KEY={Your OpenAI API Key here}
```
```bash
$ export TAVILY_API_KEY={Your Tavily API Key here}
```

- **LLMには、[OpenAI GPT](https://platform.openai.com/docs/guides/gpt) を使用することをお勧めします**が、[Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai) がサポートする他の LLM モデル（オープンソースを含む）を使用することもできます。llm モデルとプロバイダーを config/config.py で変更するだけです。[このガイド](https://python.langchain.com/docs/integrations/llms/) に従って、LLM を Langchain と統合する方法を学んでください。
- **検索エンジンには、[Tavily Search API](https://app.tavily.com)（LLM 用に最適化されています）を使用することをお勧めします**が、他の検索エンジンを選択することもできます。config/config.py で検索プロバイダーを「duckduckgo」、「googleAPI」、「googleSerp」、「searx」に変更するだけです。次に、config.py ファイルに対応する env API キーを追加します。
- **最適なパフォーマンスを得るために、[OpenAI GPT](https://platform.openai.com/docs/guides/gpt) モデルと [Tavily Search API](https://app.tavily.com) を使用することを強くお勧めします。**
<br />

> **ステップ 4** - FastAPI を使用してエージェントを実行します

```bash
$ uvicorn main:app --reload
```
<br />

> **ステップ 5** - 任意のブラウザで http://localhost:8000 にアクセスして、リサーチを楽しんでください！

Docker の使い方や機能とサービスの詳細については、[ドキュメント](https://docs.gptr.dev) ページをご覧ください。

## 🚀 貢献
私たちは貢献を大歓迎します！興味がある場合は、[貢献](CONTRIBUTING.md) をご覧ください。

私たちの[ロードマップ](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) ページを確認し、私たちの使命に参加することに興味がある場合は、[Discord コミュニティ](https://discord.gg/QgZXvJAccX) を通じてお問い合わせください。

## ✉️ サポート / お問い合わせ
- [コミュニティディスカッション](https://discord.gg/spBgZmm3Xe)
- 私たちのメール: support@tavily.com

## 🛡 免責事項

このプロジェクト「GPT Researcher」は実験的なアプリケーションであり、明示または黙示のいかなる保証もなく「現状のまま」提供されます。私たちは学術目的のためにMITライセンスの下でコードを共有しています。ここに記載されている内容は学術的なアドバイスではなく、学術論文や研究論文での使用を推奨するものではありません。

私たちの客観的な研究主張に対する見解：
1. 私たちのスクレイピングシステムの主な目的は、不正確な事実を減らすことです。どうやって解決するのか？私たちがスクレイピングするサイトが多ければ多いほど、誤ったデータの可能性は低くなります。各研究で20の情報を収集し、それらがすべて間違っている可能性は非常に低いです。
2. 私たちの目標はバイアスを排除することではなく、可能な限りバイアスを減らすことです。**私たちはここでコミュニティとして最も効果的な人間と機械の相互作用を探求しています**。
3. 研究プロセスでは、人々も自分が研究しているトピックに対してすでに意見を持っているため、バイアスがかかりやすいです。このツールは多くの意見を収集し、偏った人が決して読まないであろう多様な見解を均等に説明します。

**GPT-4 言語モデルの使用は、トークンの使用により高額な費用がかかる可能性があることに注意してください**。このプロジェクトを利用することで、トークンの使用状況と関連する費用を監視および管理する責任があることを認めたことになります。OpenAI API の使用状況を定期的に確認し、予期しない料金が発生しないように必要な制限やアラートを設定することを強くお勧めします。

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
