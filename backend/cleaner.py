import re
import html
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import spacy
from dateutil import parser as date_parser

# add ArticleMetaData here, once made
try:
    nlp = spacy.load("en_core_web_sm")
    # remove nlp features if we're not able to access this model
except:
    nlp = None


# list of content that can be cleaned up
NAV_PATTERNS = [
    r'\b(Home|About|Contact|Privacy Policy|Terms of Service|FAQ|Search)\b',
    r'\b(Menu|Navigation|Breadcrumb|Sitemap)\b',
    r'You are here:?.*?(?=\n|$)',
    r'Home\s*[>»›]\s*\w+(?:\s*[>»›]\s*\w+)*',
]

SOCIAL_PATTERNS = [
    r'\b(Share|Tweet|Like|Follow|Subscribe)\b',
    r'\b(Facebook|Twitter|LinkedIn|Instagram|Pinterest|Reddit)\b',
    r'Share this:?.*?(?=\n|$)',
    r'Follow us on.*?(?=\n|$)',
]

CTA_PATTERNS = [
    r'\b(Subscribe|Sign up|Register|Join|Download|Get Started|Learn More|Read More|Click Here)\b',
    r'Enter your email.*?(?=\n|$)',
    r'Join our newsletter.*?(?=\n|$)',
]

# need to add a mechanism to not scrape content inside a comment
COMMENT_PATTERNS = [
    r'Comments?:?.*?(?=\n\n|$)',
    r'\d+\s+comments?',
    r'Leave a comment.*?(?=\n|$)',
    r'Post a comment.*?(?=\n|$)',
]

PROMO_PATTERNS = [
    r'\b(Advertisement|Sponsored|Promoted|Ad\b)',
    r'This post contains affiliate links',
    r'Disclosure:.*?(?=\n\n|$)',
    r'Partner content',
]

COOKIE_PATTERNS = [
    r'We use cookies.*?(?=\n\n|$)',
    r'This website uses cookies.*?(?=\n\n|$)',
    r'By continuing to use.*?(?=\n\n|$)',
    r'Accept cookies.*?(?=\n|$)',
]

CITATION_PATTERN = r'\[\d+\]'

# if missed by unescape, can use these to normalize
HTML_ENTITIES = [
    ('&nbsp;', ' '),
    ('&amp;', '&'),
    ('&lt;', '<'),
    ('&gt;', '>'),
    ('&quot;', '"'),
    ('&apos;', "'"),
    ('&#39;', "'"),
    ('&mdash;', '—'),
    ('&ndash;', '–'),
    ('&hellip;', '...'),
]

def clean_text(raw_text: str) -> str:
    # empty input should return empty string
    if not raw_text:
        return ""
    
    text = raw_text
    
    for pattern in NAV_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    for pattern in SOCIAL_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    for pattern in CTA_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    for pattern in COMMENT_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    for pattern in COOKIE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    for pattern in PROMO_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # convert escaped html to normal text
    text = html.unescape(text)
    
    for entity, replacement in HTML_ENTITIES:
        text = text.replace(entity, replacement)
    
    sentences = text.split('.')
    cleaned_sentences = []
    
    # handle citations
    for sentence in sentences:
        if not re.search(CITATION_PATTERN, sentence) or len(sentence.strip()) > 50:
            cleaned_sentences.append(sentence)
        else:
            cleaned_sentence = re.sub(CITATION_PATTERN, '', sentence)
            if cleaned_sentence.strip():
                cleaned_sentences.append(cleaned_sentence)
    text = '.'.join(cleaned_sentences)
    
    # removing any weird uneven spacing or indents, or even line breaks
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    
    text = '\n'.join(line.strip() for line in text.split('\n'))
    
    text = text.strip()
    
    return text

def remove_promotional_content(text: str) -> str:
    if not text:
        return ""
    
    cleaned = text
    
    for pattern in PROMO_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        line_lower = line.lower()
        if not any(keyword in line_lower for keyword in 
                   ['advertisement', 'sponsored', 'affiliate', 'promotion', 'banner']):
            filtered_lines.append(line)
    
    cleaned = '\n'.join(filtered_lines)
    
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


def extract_metadata(raw_text: str, html: str = "") -> Dict:
    metadata = {
        'publish_date': None,
        'author': None,
        'author_bio': None,
        'tags': [],
        'categories': [],
        'reading_time': None,
        'word_count': None
    }
    
    if html:
        date_match = re.search(
            r'<time[^>]*datetime=["\']([^"\']+)["\'][^>]*>',
            html,
            re.IGNORECASE
        )
        if date_match:
            try:
                parsed_date = date_parser.parse(date_match.group(1))
                metadata['publish_date'] = parsed_date.isoformat()
            except:
                pass
        
        if not metadata['publish_date']:
            date_patterns = [
                r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
                r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    try:
                        parsed_date = date_parser.parse(match.group(1))
                        metadata['publish_date'] = parsed_date.isoformat()
                        break
                    except:
                        pass
        
        author_match = re.search(
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
            html,
            re.IGNORECASE
        )
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        if not metadata['author']:
            author_patterns = [
                r'<span[^>]*class=["\'][^"\']*author[^"\']*["\'][^>]*>([^<]+)</span>',
                r'<a[^>]*rel=["\']author["\'][^>]*>([^<]+)</a>',
                r'By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ]
            for pattern in author_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    metadata['author'] = match.group(1).strip()
                    break
        
        bio_match = re.search(
            r'<div[^>]*class=["\'][^"\']*author-bio[^"\']*["\'][^>]*>([^<]+)</div>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        if bio_match:
            bio_text = re.sub(r'<[^>]+>', '', bio_match.group(1))
            metadata['author_bio'] = bio_text.strip()[:500]
        
        tag_patterns = [
            r'<meta[^>]*property=["\']article:tag["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
            r'<a[^>]*rel=["\']tag["\'][^>]*>([^<]+)</a>',
        ]
        tags_set = set()
        for pattern in tag_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                tag = match.group(1).strip()
                if tag:
                    tags_set.add(tag)
        metadata['tags'] = list(tags_set)
        
        category_patterns = [
            r'<meta[^>]*property=["\']article:section["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
            r'<a[^>]*rel=["\']category["\'][^>]*>([^<]+)</a>',
        ]
        categories_set = set()
        for pattern in category_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                category = match.group(1).strip()
                if category:
                    categories_set.add(category)
        metadata['categories'] = list(categories_set)
        
        reading_time_match = re.search(
            r'(\d+)\s*(?:min|minute)s?\s*read',
            html,
            re.IGNORECASE
        )
        if reading_time_match:
            metadata['reading_time'] = int(reading_time_match.group(1))
    
    if raw_text:
        words = raw_text.split()
        metadata['word_count'] = len(words)
        
        if not metadata['reading_time'] and metadata['word_count']:
            metadata['reading_time'] = max(1, metadata['word_count'] // 200)
    
    if not metadata['publish_date'] and raw_text:
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, raw_text)
            if match:
                try:
                    parsed_date = date_parser.parse(match.group(1))
                    metadata['publish_date'] = parsed_date.isoformat()
                    break
                except:
                    pass
    
    if not metadata['author'] and raw_text and nlp:
        doc = nlp(raw_text[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                metadata['author'] = ent.text
                break
    
    return metadata