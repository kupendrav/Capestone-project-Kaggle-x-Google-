import os
import time
import json
import logging
from dataclasses import dataclass
from typing import List, Dict
import difflib

# Optional GenAI
try:
    import google.generativeai as genai
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False

import arxiv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger('paper_agent')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if _HAS_GENAI and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info('Configured google.generativeai')
    except Exception as e:
        logger.warning('Failed to configure google.generativeai: %s', e)
        _HAS_GENAI = False

SESSION_DIR = 'sessions'
os.makedirs(SESSION_DIR, exist_ok=True)

# Session helpers

def save_session(session_id: str, data: Dict):
    path = os.path.join(SESSION_DIR, f'{session_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info('Saved session %s', session_id)


def load_session(session_id: str) -> Dict:
    path = os.path.join(SESSION_DIR, f'{session_id}.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Context compaction

def compact_context(title: str, papers: List[Dict], max_chars: int = 4000) -> str:
    title_tokens = set(t.lower() for t in title.split())
    def score(p):
        text = (p.get('title','') + ' ' + p.get('abstract','')).lower()
        return sum(1 for tok in title_tokens if tok in text)
    papers_sorted = sorted(papers, key=score, reverse=True)
    out = ''
    for p in papers_sorted:
        chunk = f"Title: {p.get('title')}\nAuthors: {p.get('authors')}\nAbstract: {p.get('abstract')}\nURL: {p.get('url')}\n\n"
        if len(out) + len(chunk) > max_chars:
            break
        out += chunk
    return out

# Models

@dataclass
class Paper:
    title: str
    authors: str
    abstract: str
    url: str

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
    def run(self, *args, **kwargs):
        raise NotImplementedError()

# Agents

class ResearchAgent(BaseAgent):
    """Searches arXiv and returns a list of dicts with title/authors/abstract/url"""
    def __init__(self, max_results=5):
        super().__init__('ResearchAgent')
        self.max_results = max_results

    def run(self, query: str) -> List[Dict]:
        logger.info('ResearchAgent searching arXiv for query: %s', query)
        try:
            search = arxiv.Search(query=query, max_results=self.max_results, sort_by=arxiv.SortCriterion.Relevance)
            results = []
            for r in search.results():
                results.append({
                    'title': r.title,
                    'authors': ', '.join([a.name for a in r.authors]),
                    'abstract': (r.summary or '').replace('\n', ' '),
                    'url': r.entry_id
                })
            logger.info('ResearchAgent found %d papers', len(results))
            return results
        except Exception as e:
            logger.exception('ResearchAgent failed: %s', e)
            return []

class WriterAgent(BaseAgent):
    """Generates a draft paper. Uses Gemini/GenAI if available, otherwise a template-based writer."""
    def __init__(self):
        super().__init__('WriterAgent')

    def run(self, title: str, context: str) -> str:
        logger.info('WriterAgent generating draft for: %s', title)
        prompt = f"Write a detailed academic paper in IMRaD format for the title: '{title}'. Include Abstract, Introduction, Methods, Results, Discussion, Conclusion, and References. Use the following research context:\n{context}"
        if _HAS_GENAI:
            try:
                resp = genai.GenerativeModel('gemini-pro').generate_content(prompt)
                return resp.text
            except Exception as e:
                logger.warning('GenAI write failed, falling back to template: %s', e)

        # Fallback template
        abstract = context[:800].strip() or ('This paper discusses ' + title)
        intro = f"Introduction:\nThis paper addresses {title}. Context and related work: {context[:1500]}"
        methods = 'Methods:\nThis is a simulated demo. Methods would include literature review and synthesis.'
        results = 'Results:\nThis notebook produces a synthetic paper draft based on retrieved abstracts.'
        discussion = 'Discussion:\nInterpretation of results and limitations.'
        conclusion = 'Conclusion:\nSummary and future work.'
        references = 'References:\n(See arXiv links in context.)'
        paper = f"Abstract:\n{abstract}\n\n{intro}\n\n{methods}\n\n{results}\n\n{discussion}\n\n{conclusion}\n\n{references}"
        return paper

class EditorAgent(BaseAgent):
    def __init__(self):
        super().__init__('EditorAgent')

    def run(self, paper_text: str) -> str:
        logger.info('EditorAgent editing paper (lightweight edits)')
        text = paper_text.strip()
        for h in ['Abstract:', 'Introduction:', 'Methods:', 'Results:', 'Discussion:', 'Conclusion:', 'References:']:
            if h not in text:
                text = h + '\n' + text
        lines = [l.rstrip() for l in text.splitlines()]
        cleaned = []
        prev_blank = False
        for l in lines:
            if not l:
                if not prev_blank:
                    cleaned.append('')
                prev_blank = True
            else:
                cleaned.append(l)
                prev_blank = False
        return '\n'.join(cleaned)

class PlagiarismAgent(BaseAgent):
    def __init__(self):
        super().__init__('PlagiarismAgent')

    def run(self, paper_text: str, source_abstracts: List[str]) -> Dict:
        logger.info('PlagiarismAgent comparing paper against %d source abstracts', len(source_abstracts))
        scores = []
        for a in source_abstracts:
            try:
                s = difflib.SequenceMatcher(None, paper_text, a).ratio()
            except Exception:
                s = 0.0
            scores.append(s)
        max_score = max(scores) if scores else 0.0
        avg_score = sum(scores)/len(scores) if scores else 0.0
        report = {
            'max_similarity': round(max_score*100,2),
            'avg_similarity': round(avg_score*100,2),
            'flags': ['High similarity with source abstract'] if max_score > 0.6 else []
        }
        return report

# Orchestration

def research_agent_workflow(title: str, session_id: str = None, max_results: int = 5):
    start_time = time.time()
    session_id = session_id or title.replace(' ','_')[:40]
    session = load_session(session_id) or {'title': title, 'steps': []}

    research_agent = ResearchAgent(max_results=max_results)
    t0 = time.time()
    papers = research_agent.run(title)
    dt = time.time() - t0
    session['steps'].append({'step': 'research', 'count': len(papers), 'time': dt})

    context = compact_context(title, papers)

    writer = WriterAgent()
    t0 = time.time()
    draft = writer.run(title, context)
    dt = time.time() - t0
    session['steps'].append({'step': 'draft', 'time': dt})

    editor = EditorAgent()
    t0 = time.time()
    edited = editor.run(draft)
    dt = time.time() - t0
    session['steps'].append({'step': 'edit', 'time': dt})

    plagiarism = PlagiarismAgent()
    t0 = time.time()
    abstracts = [p['abstract'] for p in papers]
    report = plagiarism.run(edited, abstracts)
    dt = time.time() - t0
    session['steps'].append({'step': 'plagiarism', 'time': dt})

    total_time = time.time() - start_time
    session['metrics'] = {'total_time': total_time, 'num_papers': len(papers)}
    session['papers'] = papers
    session['draft'] = draft[:2000]
    session['edited'] = edited[:2000]
    session['plagiarism'] = report
    save_session(session_id, session)
    logger.info('Workflow complete: total_time=%.2fs, num_papers=%d', total_time, len(papers))
    return {'session_id': session_id, 'session': session, 'draft': draft, 'edited': edited, 'plagiarism': report}

if __name__ == '__main__':
    example_title = 'The Role of AI Agents in Enhancing Academic Writing'
    out = research_agent_workflow(example_title, session_id='example_session', max_results=5)
    print('Session ID:', out['session_id'])
    print('Plagiarism report:', out['plagiarism'])
