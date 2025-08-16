#!/usr/bin/env python3
"""
Viktor Kozlov's Web Intelligence Gathering Script

A Python script that gathers current intelligence from multiple sources
and provides it to Viktor Kozlov for professional analysis.

Dependencies:
    pip install requests beautifulsoup4 feedparser python-dateutil

Usage:
    python viktor_intelligence.py --region "eastern-europe" --topics "political,security"
    python viktor_intelligence.py --briefing "morning"
    python viktor_intelligence.py --crisis "ukraine"
"""

import requests
import feedparser
import json
import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import time
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import hashlib
from collections import Counter

class OSINTGatherer:
    """Open Source Intelligence gathering system for Viktor Kozlov"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # News sources by category and region
        self.news_sources = {
            'global': [
                'https://feeds.reuters.com/reuters/topNews',
                'https://feeds.bbci.co.uk/news/world/rss.xml',
                'https://rss.cnn.com/rss/edition.rss',
                'https://feeds.npr.org/1001/rss.xml'
            ],
            'europe': [
                'https://feeds.reuters.com/reuters/UKdomesticNews',
                'https://feeds.bbci.co.uk/news/world/europe/rss.xml',
                'https://www.euronews.com/rss?level=theme&name=news'
            ],
            'middle_east': [
                'https://feeds.reuters.com/reuters/MeastPoliticsNews',
                'https://feeds.bbci.co.uk/news/world/middle_east/rss.xml',
                'https://www.aljazeera.com/xml/rss/all.xml'
            ],
            'asia': [
                'https://feeds.reuters.com/reuters/AsiaCompanyAndMarkets',
                'https://feeds.bbci.co.uk/news/world/asia/rss.xml',
                'https://www.scmp.com/rss/91/feed'
            ],
            'economics': [
                'https://feeds.reuters.com/news/economy',
                'https://feeds.ft.com/world',
                'https://feeds.bloomberg.com/markets/news.rss'
            ],
            'security': [
                'https://feeds.reuters.com/reuters/SecurityNews',
                'https://www.janes.com/feeds/defence-news.xml',
                'https://www.defensenews.com/arc/outboundfeeds/rss/'
            ]
        }
        
        # Government and official sources
        self.official_sources = {
            'us_state': 'https://www.state.gov/rss-feeds/',
            'eu_council': 'https://www.consilium.europa.eu/en/press/news/',
            'un_news': 'https://news.un.org/en/rss.xml',
            'nato': 'https://www.nato.int/rss/',
            'osce': 'https://www.osce.org/rss.xml'
        }
    
    # ================= Core Collection Methods =================
    def gather_news_by_region(self, region: str, hours_back: int = 24) -> List[Dict]:
        """Gather news from specified region in the last N hours"""
        sources = self.news_sources.get(region, self.news_sources['global'])
        articles: List[Dict[str, Any]] = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        for source_url in sources:
            try:
                self.logger.info(f"Gathering intelligence from: {source_url}")
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:10]:  # Limit to recent articles
                    pub_date = self._extract_pub_date(entry)
                    if pub_date and pub_date < cutoff_time:
                        continue
                    article = {
                        'title': entry.get('title', ''),
                        'summary': (entry.get('summary', '') or '')[:500],
                        'url': entry.get('link'),
                        'published': (pub_date or datetime.now(timezone.utc)).isoformat(),
                        'source': feed.feed.get('title', source_url),
                        'region': region,
                        'confidence_score': self._assess_source_confidence(source_url)
                    }
                    articles.append(article)
                time.sleep(0.3)  # gentle rate limiting
            except Exception as e:
                self.logger.error(f"Error gathering from {source_url}: {e}")
        return self._dedupe_articles(articles)
    
    def gather_topic_intelligence(self, topics: List[str], hours_back: int = 48) -> List[Dict]:
        """Gather intelligence on specific topics"""
        topic_sources = {t: self.news_sources[t] for t in topics if t in self.news_sources}
        articles: List[Dict[str, Any]] = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        for topic, sources in topic_sources.items():
            for source_url in sources:
                try:
                    feed = feedparser.parse(source_url)
                    for entry in feed.entries[:15]:
                        pub_date = self._extract_pub_date(entry)
                        if pub_date and pub_date < cutoff_time:
                            continue
                        full_text = f"{entry.get('title','')} {entry.get('summary','')}"
                        article = {
                            'title': entry.get('title',''),
                            'summary': (entry.get('summary','') or '')[:500],
                            'url': entry.get('link'),
                            'published': (pub_date or datetime.now(timezone.utc)).isoformat(),
                            'source': feed.feed.get('title', source_url),
                            'topic': topic,
                            'keywords': self._extract_keywords(full_text),
                            'confidence_score': self._assess_source_confidence(source_url)
                        }
                        articles.append(article)
                    time.sleep(0.3)
                except Exception as e:
                    self.logger.error(f"Error gathering topic {topic} from {source_url}: {e}")
        return self._dedupe_articles(articles)
    
    def monitor_crisis_developments(self, crisis_keywords: List[str], hours_back: int = 12) -> Dict:
        """Monitor specific crisis or developing situation"""
        crisis_intel: Dict[str, Any] = {
            'keyword_tracking': crisis_keywords,
            'monitoring_since': (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat(),
            'articles': [],
            'official_statements': [],
            'social_indicators': [],  # Placeholder for future integration
            'assessment': {
                'urgency': 'unknown',
                'credibility': 'unknown',
                'scope': 'unknown'
            }
        }
        all_sources: List[str] = []
        for source_list in self.news_sources.values():
            all_sources.extend(source_list)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        collected: List[Dict[str, Any]] = []
        for source_url in all_sources[:20]:  # Limit sources for crisis monitoring
            try:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:10]:
                    title_text = entry.get('title','').lower()
                    summary_text = entry.get('summary','').lower()
                    if not any(kw.lower() in title_text or kw.lower() in summary_text for kw in crisis_keywords):
                        continue
                    pub_date = self._extract_pub_date(entry)
                    if pub_date and pub_date < cutoff_time:
                        continue
                    text = f"{entry.get('title','')} {entry.get('summary','')}"
                    urgency = self._assess_urgency(text)
                    article = {
                        'title': entry.get('title',''),
                        'summary': (entry.get('summary','') or '')[:500],
                        'url': entry.get('link'),
                        'published': (pub_date or datetime.now(timezone.utc)).isoformat(),
                        'source': feed.feed.get('title', source_url),
                        'matched_keywords': [kw for kw in crisis_keywords if kw.lower() in title_text or kw.lower() in summary_text],
                        'urgency_indicators': urgency,
                        'confidence_score': self._assess_source_confidence(source_url)
                    }
                    collected.append(article)
                time.sleep(0.2)
            except Exception as e:
                self.logger.error(f"Error gathering crisis intel from {source_url}: {e}")
        collected = self._dedupe_articles(collected)
        crisis_intel['articles'] = collected
        # Basic assessment synthesis
        if collected:
            # Urgency: take max level
            urgency_levels = [a['urgency_indicators']['level_score'] for a in collected if 'urgency_indicators' in a]
            max_urg = max(urgency_levels) if urgency_levels else 0
            crisis_intel['assessment']['urgency'] = 'high' if max_urg > 0.7 else 'medium' if max_urg > 0.4 else 'low'
            # Credibility: average confidence score
            conf_scores = [a.get('confidence_score', 0.5) for a in collected]
            avg_conf = sum(conf_scores)/len(conf_scores)
            crisis_intel['assessment']['credibility'] = 'high' if avg_conf > 0.75 else 'moderate' if avg_conf > 0.5 else 'low'
            # Scope: number of distinct sources & keywords
            distinct_sources = {a['source'] for a in collected}
            distinct_keywords = {kw for a in collected for kw in a.get('matched_keywords', [])}
            scope_score = len(distinct_sources) + len(distinct_keywords)/10
            crisis_intel['assessment']['scope'] = 'broad' if scope_score > 10 else 'developing' if scope_score > 5 else 'limited'
        return crisis_intel

    # ================= Helper Methods =================
    def _extract_pub_date(self, entry: Any) -> Optional[datetime]:
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if 'updated_parsed' in entry and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            return None
        return None

    def _extract_keywords(self, text: str, top_n: int = 8) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = [t for t in text.split() if 3 <= len(t) <= 20]
        stop = {
            'the','and','for','that','with','from','this','have','has','will','but','not','are','was','were','its','their','into','over','after','amid','amidst','more','than','into','said','new'
        }
        tokens = [t for t in tokens if t not in stop]
        freq = Counter(tokens)
        return [w for w,_ in freq.most_common(top_n)]

    def _assess_source_confidence(self, url: str) -> float:
        url_l = url.lower()
        if any(k in url_l for k in ['reuters','bbc','bloomberg','ft.com','nato.int','un.org']):
            base = 0.85
        elif any(k in url_l for k in ['cnn','aljazeera','scmp','euronews','npr']):
            base = 0.75
        else:
            base = 0.6
        # Could extend with historical reliability metrics
        return round(base, 3)

    def _assess_urgency(self, text: str) -> Dict[str, Any]:
        patterns = {
            'escalation': r'\b(attack|offensive|strike|launched|troop|mobiliz|shelling|airstrike)\b',
            'casualties': r'\b(\d+\s+(killed|dead|injured|wounded|casualties))\b',
            'immediacy': r'\b(breaking|urgent|just in|developing)\b',
            'diplomatic': r'\b(sanction|talks|negotiation|ceasefire|diplomat)\b'
        }
        scores = []
        findings = {}
        ltext = text.lower()
        for k, pat in patterns.items():
            found = re.findall(pat, ltext)
            findings[k] = len(found)
            if found:
                scores.append(min(0.4, 0.1 * len(found)))
        level_score = min(1.0, sum(scores)) if scores else 0.0
        return {'findings': findings, 'level_score': level_score}

    def _dedupe_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for a in sorted(articles, key=lambda x: x.get('published',''), reverse=True):
            key_raw = (a.get('url') or '') + (a.get('title') or '')
            h = hashlib.sha256(key_raw.encode('utf-8')).hexdigest()[:16]
            if h in seen:
                continue
            seen.add(h)
            deduped.append(a)
        return deduped

    # ================= Summarization Stub (for LLM integration) =================
    def build_brief(self, articles: List[Dict[str, Any]], max_items: int = 20) -> str:
        """Return a concise markdown brief for LLM context"""
        sel = articles[:max_items]
        lines = ["# Intelligence Brief", f"Generated: {datetime.now(timezone.utc).isoformat()}"]
        for idx, a in enumerate(sel, 1):
            lines.append(f"{idx}. {a.get('title')} ({a.get('source')}, {a.get('published')})\n   {a.get('summary')}")
        return "\n".join(lines)

# ================= CLI =================

def parse_args():
    p = argparse.ArgumentParser(description="OSINT collection for Kozlov LLM")
    p.add_argument('--region', help='Region to gather', default=None)
    p.add_argument('--topics', help='Comma-separated topics', default=None)
    p.add_argument('--crisis', help='Comma-separated crisis keywords', default=None)
    p.add_argument('--hours', help='Lookback hours (default varies)', type=int, default=None)
    p.add_argument('--output', help='Output JSON file', default=None)
    p.add_argument('--brief', action='store_true', help='Emit markdown brief to stdout')
    p.add_argument('-v','--verbose', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='[%(levelname)s] %(message)s')
    g = OSINTGatherer()
    result: Dict[str, Any] = {'generated': datetime.now(timezone.utc).isoformat()}

    if args.region:
        hours = args.hours or 24
        region_articles = g.gather_news_by_region(args.region, hours_back=hours)
        result['region'] = {'name': args.region, 'articles': region_articles}
    if args.topics:
        topics = [t.strip() for t in args.topics.split(',') if t.strip()]
        hours = args.hours or 48
        topic_articles = g.gather_topic_intelligence(topics, hours_back=hours)
        result['topics'] = {'requested': topics, 'articles': topic_articles}
    if args.crisis:
        crisis_keywords = [c.strip() for c in args.crisis.split(',') if c.strip()]
        hours = args.hours or 12
        crisis = g.monitor_crisis_developments(crisis_keywords, hours_back=hours)
        result['crisis'] = crisis

    # Build combined list for optional brief
    all_articles: List[Dict[str, Any]] = []
    for section in ['region', 'topics', 'crisis']:
        sec = result.get(section)
        if not sec:
            continue
        if section == 'crisis':
            all_articles.extend(sec.get('articles', []))
        else:
            all_articles.extend(sec.get('articles', []))

    if args.brief and all_articles:
        brief_md = g.build_brief(all_articles)
        print(brief_md)

    # Always output JSON (stdout or file)
    output_json = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        logging.info(f"Wrote JSON to {args.output}")
    else:
        print(output_json)

if __name__ == '__main__':
    main()