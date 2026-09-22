"""Deterministic Markdown measurements and conservative preservation checks.

Parsing is local and inert: this module does not render HTML, resolve URLs, read
included files, or execute document content. Readability is an English heuristic,
not a grammar, factual-accuracy, or semantic-equivalence judgment.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from importlib.metadata import version
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline.backticks import backtick
from markdown_it.rules_inline.state_inline import StateInline
from markdown_it.token import Token

_WORD = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
_SENTENCE_BOUNDARY = re.compile(r"[.!?]+[\"'”’)]*\s+")
_QUANTITY = re.compile(
    r"(?<![\w.])(?:[$€£¥]\s*)?[+-]?\d+(?:[.,]\d+)*(?:[eE][+-]?\d+)?"
    r"(?:\s*(?:%|°[CF]\b|(?:ns|us|µs|ms|seconds?|secs?|minutes?|mins?|hours?|hrs?|"
    r"days?|weeks?|months?|years?|[KMGTPE]?i?B|bytes?|bits?|[kMGT]?Hz|"
    r"[munck]?m|[munck]?g|[mun]?l|USD|EUR|GBP|CAD|PHP)\b))?",
    re.IGNORECASE,
)
_MODAL = re.compile(
    r"\b(?:must(?:\s+not)?|shall(?:\s+not)?|should(?:\s+not)?|may(?:\s+not)?|"
    r"cannot|can|requires?|required|recommended|optional|prohibited)\b",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"\b(?:not|no|never|without|cannot|neither|nor|[a-z]+n['’]t)\b", re.IGNORECASE
)
_HARD_CATEGORIES = (
    "code_blocks",
    "inline_code",
    "link_destinations",
    "reference_definitions",
    "frontmatter",
    "raw_html",
)
_REVIEW_CATEGORIES = ("quantities", "requirement_modals", "negations", "headings")
LIMITATIONS = [
    "CommonMark plus tables is parsed; other GFM extensions, MDX, directives, and embedded "
    "languages are not fully understood.",
    "Sections use document-level ATX and setext headings; headings inside quotes or lists "
    "do not open sections. Line ranges are one-based and inclusive.",
    "Readability counts visible inline prose, including headings, table cells, and image alt "
    "text; code, raw HTML blocks, reference definitions, and recognized frontmatter are excluded.",
    "Sentence boundaries, English word and syllable counts, and Flesch scores are approximate; "
    "abbreviations, non-English prose, names, and technical terms can distort them.",
    "Link destinations are parser-normalized values. Inline code source follows the parser's "
    "newline and container normalization; block code and reference source preserve input lines.",
    "Frontmatter recognition is a local convention for a closed YAML or TOML block at the "
    "start, not CommonMark syntax; an initial thematic-break region can be classified as metadata.",
    "Heading changes flag potential anchor regressions; CommonMark does not specify generated "
    "anchors, so renderer-specific link checks are required to establish whether links break.",
    "Quantity, modal, and negation inventories are lexical warnings. Equal inventories can "
    "hide changed relationships, scope, order, or negation; they never prove preserved meaning.",
    "No grammar, factual validity, URL reachability, or automatic acceptance is established.",
]


def _source_lines(text: str) -> list[str]:
    """Match the parser's CR/LF line handling while retaining original line endings."""
    lines = re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", text)
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _inline_code_source(state: StateInline, silent: bool) -> bool:
    start, token_count = state.pos, len(state.tokens)
    matched = backtick(state, silent)
    if matched and not silent:
        for token in state.tokens[token_count:]:
            if token.type == "code_inline":
                token.meta["source"] = state.src[start : state.pos]
    return matched


def _parser() -> MarkdownIt:
    parser = MarkdownIt("commonmark", {"inline_definitions": True}).enable("table")
    parser.inline.ruler.at("backticks", _inline_code_source)
    return parser


def _frontmatter(lines: list[str]) -> tuple[int, list[dict[str, str]]]:
    if not lines:
        return 0, []
    opening = lines[0].rstrip("\r\n").removeprefix("\ufeff")
    if opening not in {"---", "+++"}:
        return 0, []
    closers = {"---", "..."} if opening == "---" else {"+++"}
    for index, line in enumerate(lines[1:], 1):
        if line.rstrip("\r\n") in closers:
            return index + 1, [
                {
                    "format": "yaml" if opening == "---" else "toml",
                    "text": "".join(lines[: index + 1]),
                }
            ]
    return 0, []


def _visible_text(tokens: list[Token]) -> str:
    parts: list[str] = []
    for token in tokens:
        if token.type == "text":
            parts.append(token.content)
        elif token.type in {"softbreak", "hardbreak", "code_inline", "html_inline"}:
            parts.append(" ")
        elif token.type == "image":
            parts.append(_visible_text(token.children or []))
    return "".join(parts)


def _walk_inline(tokens: list[Token]) -> list[Token]:
    result: list[Token] = []
    for token in tokens:
        result.append(token)
        if token.children:
            result.extend(_walk_inline(token.children))
    return result


def _heading_title(inline: Token) -> str:
    return "".join(
        child.content if child.type == "code_inline" else _visible_text([child])
        for child in inline.children or []
    ).strip()


def _syllables(word: str) -> int:
    """Vowel-group estimate with simple English suffix adjustments, not a dictionary."""
    lowered = word.lower().replace("’", "'")
    groups = len(re.findall(r"[aeiouy]+", lowered))
    if lowered.endswith("e") and not lowered.endswith(("le", "ye")) and groups > 1:
        groups -= 1
    if lowered.endswith("ed") and not lowered.endswith(("ted", "ded")) and groups > 1:
        groups -= 1
    return max(1, groups)


def _metrics(tokens: list[Token], start: int, end: int) -> dict[str, Any]:
    selected = [token for token in tokens if token.map and start <= token.map[0] < end]
    blocks = [_visible_text(token.children or []) for token in selected if token.type == "inline"]
    words = [word for block in blocks for word in _WORD.findall(block)]
    sentences = [
        sentence.strip()
        for block in blocks
        for sentence in _SENTENCE_BOUNDARY.split(block)
        if _WORD.search(sentence)
    ]
    sentence_lengths = [len(_WORD.findall(sentence)) for sentence in sentences]
    paragraph_lengths: list[int] = []
    for index, token in enumerate(tokens):
        if token.type != "paragraph_open" or not token.map or not start <= token.map[0] < end:
            continue
        if index + 1 < len(tokens) and tokens[index + 1].type == "inline":
            paragraph_lengths.append(
                len(_WORD.findall(_visible_text(tokens[index + 1].children or [])))
            )

    word_count, sentence_count = len(words), len(sentences)
    syllable_count = sum(_syllables(word) for word in words)
    mean_sentence = word_count / sentence_count if sentence_count else None
    mean_paragraph = sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else None
    if word_count and sentence_count:
        words_per_sentence = word_count / sentence_count
        syllables_per_word = syllable_count / word_count
        ease = round(206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word, 2)
        grade = round(0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59, 2)
    else:
        ease = grade = None
    normalized = Counter(
        " ".join(word.casefold() for word in _WORD.findall(sentence))
        for sentence in sentences
        if len(_WORD.findall(sentence)) >= 4
    )
    return {
        "word_count": word_count,
        "word_character_counts": [len(word) for word in words],
        "mean_characters_per_word": round(sum(map(len, words)) / word_count, 2) if words else None,
        "sentence_count": sentence_count,
        "paragraph_count": len(paragraph_lengths),
        "sentence_word_counts": sentence_lengths,
        "paragraph_word_counts": paragraph_lengths,
        "mean_words_per_sentence": round(mean_sentence, 2) if mean_sentence is not None else None,
        "mean_words_per_paragraph": round(mean_paragraph, 2)
        if mean_paragraph is not None
        else None,
        "heading_depths": [
            int(token.tag[1:])
            for token in selected
            if token.type == "heading_open" and token.level == 0
        ],
        "readability": {
            "method": "approximate English Flesch/Flesch-Kincaid using heuristic vowel-group syllables",
            "syllable_count": syllable_count,
            "flesch_reading_ease": ease,
            "flesch_kincaid_grade": grade,
        },
        "repeated_sentences": [
            {"text": sentence, "occurrences": count}
            for sentence, count in sorted(normalized.items())
            if count > 1
        ],
    }


def _inventory(
    tokens: list[Token], lines: list[str], frontmatter: list[dict[str, str]]
) -> dict[str, Any]:
    inventory: dict[str, Any] = {key: [] for key in (*_HARD_CATEGORIES, *_REVIEW_CATEGORIES)}
    inventory["frontmatter"] = frontmatter
    prose: list[str] = []
    for index, token in enumerate(tokens):
        source = "".join(lines[token.map[0] : token.map[1]]) if token.map else token.content
        if token.type in {"fence", "code_block"}:
            inventory["code_blocks"].append(
                {"kind": token.type, "info": token.info, "text": token.content, "source": source}
            )
        elif token.type == "definition":
            inventory["reference_definitions"].append(
                {
                    "label": token.meta["label"],
                    "destination": token.meta["url"],
                    "title": token.meta["title"],
                    "source": source,
                }
            )
        elif token.type == "html_block":
            inventory["raw_html"].append({"kind": token.type, "text": source})
        elif token.type == "heading_open" and token.level == 0:
            inventory["headings"].append(
                {"depth": int(token.tag[1:]), "title": _heading_title(tokens[index + 1])}
            )
        elif token.type == "inline":
            prose.append(_visible_text(token.children or []))
            for child in _walk_inline(token.children or []):
                if child.type == "code_inline":
                    inventory["inline_code"].append(
                        {"text": child.content, "source": child.meta.get("source", child.content)}
                    )
                elif child.type in {"link_open", "image"}:
                    inventory["link_destinations"].append(
                        {
                            "kind": "image" if child.type == "image" else "link",
                            "destination": child.attrGet(
                                "src" if child.type == "image" else "href"
                            ),
                            "title": child.attrGet("title") or "",
                        }
                    )
                elif child.type == "html_inline":
                    inventory["raw_html"].append({"kind": child.type, "text": child.content})
    visible = "\n".join(prose)
    inventory["quantities"] = [
        re.sub(r"\s+", " ", match.group()) for match in _QUANTITY.finditer(visible)
    ]
    inventory["requirement_modals"] = [
        re.sub(r"\s+", " ", match.group().casefold()) for match in _MODAL.finditer(visible)
    ]
    inventory["negations"] = [match.group().casefold() for match in _NEGATION.finditer(visible)]
    return inventory


def analyze_document(text: str) -> dict[str, Any]:
    """Measure Markdown and return disjoint source sections plus protected inventories."""
    lines = _source_lines(text)
    frontmatter_end, frontmatter = _frontmatter(lines)
    # Blank lines retain source positions, while metadata is kept out of prose metrics.
    parse_text = "\n" * frontmatter_end + "".join(lines[frontmatter_end:])
    tokens = _parser().parse(parse_text)
    headings: list[tuple[int, str, list[str]]] = []
    hierarchy: list[tuple[int, str]] = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.level != 0 or token.map is None:
            continue
        title = _heading_title(tokens[index + 1])
        depth = int(token.tag[1:])
        while hierarchy and hierarchy[-1][0] >= depth:
            hierarchy.pop()
        hierarchy.append((depth, title))
        headings.append((token.map[0], title, [item[1] for item in hierarchy]))
    starts: list[tuple[int, str, list[str]]] = []
    preamble_end = headings[0][0] if headings else len(lines)
    if "".join(lines[:preamble_end]).strip():
        starts.append((0, "", []))
    starts.extend(headings)
    sections: list[dict[str, Any]] = []
    for index, (start, title, path) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        sections.append(
            {
                "id": f"section-{start + 1}",
                "title": title,
                "heading_path": path,
                "start_line": start + 1,
                "end_line": end,
                "text": "".join(lines[start:end]),
                "metrics": _metrics(tokens, start, end),
            }
        )
    return {
        "schema_version": 1,
        "parser": {
            "name": "markdown-it-py",
            "version": version("markdown-it-py"),
            "preset": "commonmark",
            "extensions": ["table"],
        },
        "metrics": _metrics(tokens, 0, len(lines)),
        "sections": sections,
        "protected": _inventory(tokens, lines, frontmatter),
        "limitations": list(LIMITATIONS),
    }


def _inventory_difference(original: list[Any], revised: list[Any]) -> dict[str, Any]:
    before = Counter(json.dumps(item, sort_keys=True, ensure_ascii=False) for item in original)
    after = Counter(json.dumps(item, sort_keys=True, ensure_ascii=False) for item in revised)
    removed_counts, added_counts = before - after, after - before

    def entries(counts: Counter[str]) -> list[dict[str, Any]]:
        return [
            {"value": json.loads(value), "count": count} for value, count in sorted(counts.items())
        ]

    return {
        "status": "unchanged" if original == revised else "changed",
        "added_count": sum(added_counts.values()),
        "removed_count": sum(removed_counts.values()),
        "added": entries(added_counts),
        "removed": entries(removed_counts),
        "sequence_changed": original != revised,
    }


def compare_documents(original: str, revised: str) -> dict[str, Any]:
    """Report preservation changes; unchanged inventories are never semantic proof."""
    before = analyze_document(original)["protected"]
    after = analyze_document(revised)["protected"]
    hard_checks = {key: _inventory_difference(before[key], after[key]) for key in _HARD_CATEGORIES}
    review_checks = {
        key: _inventory_difference(before[key], after[key]) for key in _REVIEW_CATEGORIES
    }
    changed = original != revised
    return {
        "schema_version": 1,
        "status": "needs_review" if changed else "unchanged",
        "text_changed": changed,
        "meaning_preservation": "not_established",
        "hard_preservation": {
            "status": "changed"
            if any(row["status"] == "changed" for row in hard_checks.values())
            else "unchanged",
            "checks": hard_checks,
        },
        "semantic_review": {"required": changed, "checks": review_checks},
        "limitations": list(LIMITATIONS),
    }
