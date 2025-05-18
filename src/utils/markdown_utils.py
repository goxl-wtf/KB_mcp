"""Markdown Parsing and Rendering Utilities

Utilities for working with Markdown content and YAML frontmatter.
"""

import re
import yaml
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import mistune  # Markdown parser


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from Markdown content.
    
    Returns:
        Tuple of (frontmatter dict, body content)
    """
    # Check if content starts with frontmatter
    if not content.startswith('---'):
        return {}, content
    
    # Find the end of frontmatter
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return {}, content
    
    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(match.group(1))
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        print(f"Error parsing frontmatter: {e}")
        frontmatter = {}
    
    # Extract body content (everything after frontmatter)
    body = content[match.end():]
    
    return frontmatter, body


def create_frontmatter(metadata: Dict[str, Any], content: str) -> str:
    """Create Markdown content with YAML frontmatter.
    
    Args:
        metadata: Dictionary of metadata to include in frontmatter
        content: The main content of the document
    
    Returns:
        Complete Markdown document with frontmatter
    """
    # Convert metadata to YAML
    frontmatter_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    
    # Combine with content
    return f"---\n{frontmatter_str}---\n\n{content}"


def extract_links(content: str) -> Dict[str, list]:
    """Extract various types of links from Markdown content.
    
    Returns:
        Dictionary with link types as keys and lists of links as values
    """
    links = {
        'note_links': [],      # [[note_id]] style links
        'kb_links': [],        # [[kb:kb_id]] style links
        'urls': [],            # Regular URLs
        'images': [],          # Image URLs
        'references': []       # Reference-style links
    }
    
    # Extract note links [[note_id]]
    note_pattern = r'\[\[([^\]]+)\]\]'
    for match in re.finditer(note_pattern, content):
        link = match.group(1)
        if link.startswith('kb:'):
            links['kb_links'].append(link[3:])
        else:
            links['note_links'].append(link)
    
    # Extract regular URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    links['urls'] = re.findall(url_pattern, content)
    
    # Extract markdown links [text](url)
    md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(md_link_pattern, content):
        url = match.group(2)
        if url.startswith('http'):
            links['urls'].append(url)
    
    # Extract images ![alt](url)
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    for match in re.finditer(image_pattern, content):
        links['images'].append(match.group(2))
    
    # Extract reference-style links [text][ref]
    ref_pattern = r'\[([^\]]+)\]\[([^\]]+)\]'
    refs = re.findall(ref_pattern, content)
    
    # Extract reference definitions [ref]: url
    ref_def_pattern = r'^\[([^\]]+)\]:\s*(.+)$'
    for match in re.finditer(ref_def_pattern, content, re.MULTILINE):
        ref_id = match.group(1)
        url = match.group(2)
        links['references'].append({'id': ref_id, 'url': url})
    
    return links


def render_markdown(content: str, safe: bool = True) -> str:
    """Render Markdown content to HTML.
    
    Args:
        content: Markdown content to render
        safe: If True, sanitize HTML output
    
    Returns:
        Rendered HTML string
    """
    # Create Markdown parser
    if safe:
        # Use safe renderer that escapes HTML
        markdown = mistune.create_markdown(escape=True)
    else:
        # Allow raw HTML
        markdown = mistune.create_markdown(escape=False)
    
    return markdown(content)


def extract_headings(content: str) -> list:
    """Extract all headings from Markdown content.
    
    Returns:
        List of dictionaries with 'level' and 'text' keys
    """
    headings = []
    
    # Match ATX-style headings (# Heading)
    atx_pattern = r'^(#{1,6})\s+(.+)$'
    for match in re.finditer(atx_pattern, content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({'level': level, 'text': text})
    
    return headings


def create_table_of_contents(content: str, max_level: int = 3) -> str:
    """Generate a table of contents from Markdown headings.
    
    Args:
        content: Markdown content
        max_level: Maximum heading level to include
    
    Returns:
        Markdown-formatted table of contents
    """
    headings = extract_headings(content)
    toc_lines = ["## Table of Contents\n"]
    
    for heading in headings:
        if heading['level'] <= max_level:
            indent = "  " * (heading['level'] - 1)
            # Create anchor link
            anchor = heading['text'].lower().replace(' ', '-')
            anchor = re.sub(r'[^\w-]', '', anchor)
            toc_lines.append(f"{indent}- [{heading['text']}](#{anchor})")
    
    return "\n".join(toc_lines)


def update_note_links(content: str, old_id: str, new_id: str) -> str:
    """Update note links in content when a note is renamed.
    
    Args:
        content: Markdown content
        old_id: Old note ID
        new_id: New note ID
    
    Returns:
        Updated content
    """
    # Replace [[old_id]] with [[new_id]]
    pattern = rf'\[\[{re.escape(old_id)}\]\]'
    return re.sub(pattern, f'[[{new_id}]]', content)


def convert_to_wiki_links(content: str) -> str:
    """Convert standard Markdown links to wiki-style links where appropriate.
    
    Converts [Note Title](note_id) to [[note_id|Note Title]]
    """
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        text = match.group(1)
        target = match.group(2)
        
        # Only convert internal links (not URLs)
        if not target.startswith('http'):
            # Check if target looks like a note ID
            if '/' not in target and '.' not in target:
                return f'[[{target}|{text}]]'
        
        return match.group(0)
    
    return re.sub(pattern, replace_link, content)


def get_content_preview(content: str, max_length: int = 200) -> str:
    """Get a preview of Markdown content.
    
    Args:
        content: Full content
        max_length: Maximum preview length
    
    Returns:
        Preview string
    """
    # Remove frontmatter
    _, body = parse_frontmatter(content)
    
    # Remove markdown formatting for preview
    # Remove images
    preview = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', body)
    # Remove links but keep text
    preview = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', preview)
    # Remove emphasis
    preview = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', preview)
    # Remove code blocks
    preview = re.sub(r'```[^`]*```', '', preview, flags=re.DOTALL)
    # Remove inline code
    preview = re.sub(r'`([^`]+)`', r'\1', preview)
    # Remove headings markers
    preview = re.sub(r'^#{1,6}\s+', '', preview, flags=re.MULTILINE)
    
    # Clean up whitespace
    preview = ' '.join(preview.split())
    
    # Truncate if necessary
    if len(preview) > max_length:
        preview = preview[:max_length].rsplit(' ', 1)[0] + "..."
    
    return preview