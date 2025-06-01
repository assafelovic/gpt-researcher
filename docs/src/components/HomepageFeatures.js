import React from 'react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import styles from './HomepageFeatures.module.css';

const FeatureList = [
  {
    title: 'GPT Researcher',
    Svg: require('../../static/img/gptr-logo.png').default,
    docLink: './docs/gpt-researcher/getting-started',
    description: (
      <>
        GPT Researcher is an open source autonomous agent designed for comprehensive online research on a variety of tasks.
      </>
    ),
  },
  /*{
    title: 'Tavily Search API',
    Svg: require('../../static/img/tavily.png').default,
    docLink: './docs/tavily-api/introduction',
    description: (
      <>
        Tavily Search API is a search engine optimized for LLMs, optimized for a factual, efficient, and persistent search experience
      </>
    ),
  },*/
  {
    title: 'Multi-Agent Assistant',
    Svg: require('../../static/img/multi-agent.png').default,
    docLink: './docs/gpt-researcher/langgraph',
    description: (
      <>
        Learn how a team of AI agents can work together to conduct research on a given topic, from planning to publication.
      </>
    ),
  },
  {
    title: 'Examples and Demos',
    Svg: require('../../static/img/examples.png').default,
    docLink: './docs/examples/examples',
    description: (
      <>
          Check out Tavily API in action across multiple frameworks and use cases
      </>
    ),
  },
];

function Feature({Svg, title, description, docLink}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        {/*<Svg className={styles.featureSvg} alt={title} />*/}
        <img src={Svg} alt={title} height="60"/>
      </div>
      <div className="text--center padding-horiz--md">
        <Link to={docLink}>
            <h3>{title}</h3>
        </Link>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container" style={{marginTop: 30}}>
        <div className="row" style={{justifyContent: 'center'}}>
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
