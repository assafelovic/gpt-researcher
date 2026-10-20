import React, {useState} from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const INSTALL = 'pip install gpt-researcher';

const Icon = ({children}) => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

const FEATURES = [
  {
    title: 'Web research',
    body: 'Plans the questions, searches in parallel and reads 20+ sources per report, with a citation for every claim.',
    to: '/docs/gpt-researcher/getting-started/introduction',
    icon: (<Icon><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z" /></Icon>),
  },
  {
    title: 'Your documents',
    body: 'Research over PDFs, Word, spreadsheets and Markdown, on their own or combined with the web.',
    to: '/docs/gpt-researcher/context/tailored-research',
    icon: (<Icon><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></Icon>),
  },
  {
    title: 'Deep research',
    body: 'Explores a topic recursively, branching into sub-questions until the answer is thorough.',
    to: '/docs/gpt-researcher/gptr/deep_research',
    icon: (<Icon><circle cx="12" cy="5" r="2" /><circle cx="6" cy="19" r="2" /><circle cx="18" cy="19" r="2" /><path d="M12 7v4M12 11l-5 6M12 11l5 6" /></Icon>),
  },
  {
    title: 'Multi-agent teams',
    body: 'LangGraph and AG2 agents that plan, research, review and publish together.',
    to: '/docs/gpt-researcher/multi_agents/langgraph',
    icon: (<Icon><circle cx="8" cy="8" r="3" /><circle cx="16" cy="8" r="3" /><path d="M2.5 20c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5M10.5 20c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5" /></Icon>),
  },
  {
    title: 'MCP sources',
    body: 'Bring GitHub, databases and your own APIs into research through the Model Context Protocol.',
    to: '/docs/gpt-researcher/retrievers/mcp-configs',
    icon: (<Icon><path d="M9 7V3M15 7V3M7 7h10v4a5 5 0 0 1-10 0zM12 16v5" /></Icon>),
  },
  {
    title: 'Smart context',
    body: 'Jev keeps only the passages that answer the question: 59% more relevant context than embeddings.',
    to: '/docs/gpt-researcher/gptr/context-filter',
    icon: (<Icon><path d="M4 5h16l-6 7.5V19l-4 2v-8.5z" /></Icon>),
  },
];

const PAPERS = [
  {title: 'DeepResearchGym: A Free, Transparent, and Reproducible Evaluation Sandbox for Deep Research', venue: 'arXiv 2025', href: 'https://arxiv.org/abs/2505.19253'},
  {title: 'Dolphin: Moving Towards Closed-loop Auto-research through Thinking, Practice, and Feedback', venue: 'ACL 2025', href: 'https://aclanthology.org/2025.acl-long.1056/'},
  {title: 'AI for Auto-Research: Roadmap & User Guide', venue: 'arXiv 2026', href: 'https://arxiv.org/abs/2605.18661'},
  {title: 'AutoResearch AI: Towards AI-Powered Research Automation for Scientific Discovery', venue: 'arXiv 2026', href: 'https://arxiv.org/abs/2605.23204'},
  {title: 'Deep Research Comparator: A Platform for Fine-grained Human Annotations of Deep Research Agents', venue: 'ACM 2026', href: 'https://dl.acm.org/doi/abs/10.1145/3774905.3793116'},
  {title: 'Deep Researcher with Test-Time Diffusion', venue: 'arXiv 2025', href: 'https://arxiv.org/abs/2507.16075'},
];

const SCHOLAR_URL = 'https://scholar.google.com/scholar?q=%22gpt+researcher%22';

const STEPS = [
  {title: 'Plan', body: 'Breaks your question into focused sub-questions.'},
  {title: 'Search', body: 'Queries the web or your documents for each one, in parallel.'},
  {title: 'Filter', body: 'Keeps only the passages that answer each sub-question.'},
  {title: 'Write', body: 'Produces a cited report in Markdown, PDF or Word.'},
];

function CopyInstall() {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(INSTALL);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch (e) {
      /* clipboard unavailable: the command stays visible to select */
    }
  };
  return (
    <button type="button" className={styles.install} onClick={copy} aria-label="Copy install command">
      <span className={styles.prompt}>$</span>
      <code>{INSTALL}</code>
      <span className={styles.copy}>{copied ? 'Copied' : 'Copy'}</span>
    </button>
  );
}

function CodeCard() {
  return (
    <div className={styles.codeCard} aria-label="Example usage">
      <div className={styles.codeBar}>
        <span className={styles.dot} /><span className={styles.dot} /><span className={styles.dot} />
        <span className={styles.fileName}>research.py</span>
      </div>
      <pre className={styles.code}><code>
<span className={styles.kw}>from</span> gpt_researcher <span className={styles.kw}>import</span> GPTResearcher{'\n\n'}
researcher = GPTResearcher({'\n'}
{'    '}query=<span className={styles.str}>"Are solid-state batteries ready for EVs?"</span>,{'\n'}
{'    '}report_type=<span className={styles.str}>"research_report"</span>,{'\n'}
){'\n\n'}
<span className={styles.kw}>await</span> researcher.conduct_research(){'\n'}
report = <span className={styles.kw}>await</span> researcher.write_report()
      </code></pre>
      <div className={styles.codeFoot}>
        <span className={styles.ok} /> Report ready · 18 sources · 57 citations
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Layout
      title="Documentation"
      description="GPT Researcher is an open-source deep research agent that turns any question into a detailed, cited report from the web or your own documents.">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroGrid}>
            <div>
              <h1 className={styles.title}>The #1 deep research agent</h1>
              <p className={styles.lede}>
                GPT Researcher plans, searches, reads and cites. Ask a question and get a detailed,
                source-backed report, from the web or your own documents, with any LLM. Fully open
                source under the Apache 2.0 license.
              </p>
              <div className={styles.ctas}>
                <Link className={styles.primary} to="/docs/gpt-researcher/getting-started">Get started</Link>
                <Link className={styles.secondary} href="https://github.com/assafelovic/gpt-researcher">
                  GitHub <span className={styles.stars}>★ 30k</span>
                </Link>
              </div>
              <CopyInstall />
            </div>
            <CodeCard />
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.h2}>Built for real research</h2>
          <p className={styles.sub}>One agent for quick answers, long reports and everything in between.</p>
          <div className={styles.features}>
            {FEATURES.map((f) => (
              <Link key={f.title} to={f.to} className={styles.card}>
                {f.icon}
                <h3 className={styles.cardTitle}>{f.title}</h3>
                <p className={styles.cardBody}>{f.body}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.h2}>How it works</h2>
          <ol className={styles.steps}>
            {STEPS.map((s, i) => (
              <li key={s.title} className={styles.step}>
                <span className={styles.stepNum}>{String(i + 1).padStart(2, '0')}</span>
                <h3 className={styles.stepTitle}>{s.title}</h3>
                <p className={styles.stepBody}>{s.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className={styles.section}>
          <Link to="/docs/gpt-researcher/gptr/context-filter" className={styles.highlight}>
            <div>
              <div className={styles.badge}>New</div>
              <h2 className={styles.highlightTitle}>Jev’s context is 59% more relevant than embeddings, at the same cost</h2>
              <p className={styles.highlightBody}>
                GPT Researcher now filters sources with Jev by default, and falls back to local keyword
                ranking, so no key or embeddings provider is required. Read the benchmark →
              </p>
            </div>
            <div className={styles.bars} aria-hidden="true">
              {[['Jev', 73, true], ['Keyword', 51], ['Embeddings', 46]].map(([name, v, hi]) => (
                <div key={name} className={styles.barRow}>
                  <span className={styles.barName}>{name}</span>
                  <span className={styles.barTrack}><span className={hi ? styles.barFillHi : styles.barFill} style={{width: `${v}%`}} /></span>
                  <span className={styles.barValue}>{v}%</span>
                </div>
              ))}
            </div>
          </Link>
        </section>

        <section className={styles.section}>
          <div className={styles.papersHead}>
            <div>
              <h2 className={styles.h2}>Cited in 150+ research papers</h2>
              <p className={styles.sub}>Researchers use GPT Researcher as a baseline, a building block and a subject of study.</p>
            </div>
            <Link className={styles.scholar} href={SCHOLAR_URL}>All papers on Google Scholar ↗</Link>
          </div>
          <ul className={styles.papers}>
            {PAPERS.map((p) => (
              <li key={p.href}>
                <Link className={styles.paper} href={p.href}>
                  <span className={styles.paperTitle}>{p.title}</span>
                  <span className={styles.paperVenue}>{p.venue}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className={styles.cta}>
          <h2 className={styles.ctaTitle}>Start researching in five minutes</h2>
          <div className={styles.ctas}>
            <Link className={styles.primary} to="/docs/gpt-researcher/getting-started">Read the quickstart</Link>
            <Link className={styles.secondary} href="https://discord.gg/QgZXvJAccX">Join the Discord</Link>
          </div>
        </section>
      </main>
    </Layout>
  );
}
