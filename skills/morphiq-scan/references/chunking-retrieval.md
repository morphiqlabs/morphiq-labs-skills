# Chunking & Retrieval Quality Evaluation

Use this reference when evaluating how well a page's content structure supports **LLM retrieval, grounding, quoting, and citation**.

Modern AI systems often do not consume a page as one intact document. They frequently split content into smaller units, retrieve the most relevant passages, and then rerank or synthesize from those passages. Google explicitly says Search can identify and rank individual **passages** on a page, and Anthropic's retrieval guide describes standard RAG systems as chunking documents, embedding them, retrieving relevant chunks, and often reranking them before generation. ([Google for Developers](https://developers.google.com/search/docs/appearance/ranking-systems-guide))

Because of that, good AEO/GEO content is not just "good content." It is content that remains understandable after preprocessing, breaks into strong answer-bearing units, matches both semantic and exact-match retrieval, and survives reranking. Anthropic reports that combining contextual embeddings, BM25, and reranking materially improves retrieval accuracy, reducing top-20 retrieval failures by 67% in its tests. ([Anthropic](https://www.anthropic.com/research/contextual-retrieval))

## Core Principle

Evaluate each page as if an AI system will:

1. parse and simplify the page,
2. split it into chunks or passages,
3. retrieve a small set of candidate chunks,
4. rerank those chunks,
5. quote or synthesize from the winners.

A page performs well when its key claims, definitions, steps, and evidence are easy to extract as **self-contained retrieval units**. Traditional RAG often fails when a chunk lacks the local context needed to stand on its own. ([Anthropic](https://www.anthropic.com/research/contextual-retrieval))

---

## 1. Heading Hierarchy & Retrieval Anchors

### What to check

- Exactly one H1 that clearly defines the page topic
- H2s that map to major user intents, subtopics, comparisons, or questions
- H3/H4s that deepen the parent section with steps, examples, definitions, metrics, objections, or mini-FAQs
- Heading levels nested in order without skipping levels
- Headings written as specific statements or likely queries, not vague labels

### Why this matters

Headings help define chunk boundaries and retrieval anchors. If headings are vague, generic, or out of order, the section becomes harder to interpret and harder to retrieve for the right query. Google's passage system and RAG-style retrieval both reward pages whose sections are semantically well-scoped. ([Google for Developers](https://developers.google.com/search/docs/appearance/ranking-systems-guide))

### Good patterns

- `What is SOC 2 compliance?`
- `How pricing works for early-stage teams`
- `Mudra vs traditional SEO tools`
- `Implementation timeline and expected outcomes`

### Fail signals

- Multiple H1 tags
- Skipped levels such as H1 → H3
- Generic headings like `More Info`, `Overview`, `Details`, `Section 1`
- Long-form content with no headings or only visually styled text instead of semantic headings

### Score guidance

Score higher when headings are both:

- **query-aligned**: likely to match how users or systems frame retrieval queries
- **section-defining**: specific enough that the section can stand as its own retrievable unit

---

## 2. Section Scope & Chunk Boundaries

### What to check

- Each section focuses on one primary subtopic or user question
- Major topic changes happen at heading boundaries
- Sections are neither too thin nor too bloated
- Evidence needed to support a claim appears near the claim, not several sections later

### Why this matters

Chunking strategy strongly affects retrieval quality. Recent research shows chunking choices materially affect reliability, and there is no one universal "best" size; what matters is preserving coherent answer-bearing units. The same study found sentence-based chunking to be highly cost-effective and reported a "context cliff" as chunks become too large. ([Hugging Face](https://huggingface.co/papers/2601.14123))

### Practical rule

Do **not** optimize for one fixed token count alone. Optimize for **coherent retrieval units**.

A strong section:

- answers one main thing,
- includes enough nearby context to be interpretable,
- does not bury the answer under unrelated material.

### Fail signals

- One heading followed by multiple unrelated ideas
- Definitions in one paragraph and crucial qualifiers far below
- Large blended sections that cover several intents at once
- Sections that rely heavily on information only provided elsewhere on the page

---

## 3. Paragraph Quality & Local Self-Containment

### What to check

- Paragraphs generally express one main idea
- Key paragraphs can be understood without needing excessive outside context
- The subject of the paragraph is explicit
- Important entities, timeframes, products, or metrics are named locally when relevant
- Paragraphs are readable and bounded rather than wall-of-text blocks

### Why this matters

Traditional chunking often breaks context. Anthropic's example shows how a chunk like "The company's revenue grew by 3%" becomes much less retrievable when it does not say **which company** or **what period**. Retrieval quality improves when chunks contain enough local context to stand on their own. ([Anthropic](https://www.anthropic.com/research/contextual-retrieval))

### Practical rule

Prefer paragraphs that are **self-contained enough to quote**.

That does not mean every paragraph must repeat everything. It means a paragraph should not become ambiguous once separated from the full page.

### Good patterns

- "Mudra helps B2B SaaS companies improve visibility in AI search by shipping structured data, llms.txt files, and AI-optimized content."
- "For seed-stage teams, implementation typically takes 2–4 weeks depending on CMS access and schema coverage."

### Fail signals

- Pronoun-heavy paragraphs with unclear referents
- "This," "that," or "it" without a locally clear subject
- Important claims missing the entity, timeframe, product, or qualifier needed to interpret them
- Very long paragraphs mixing multiple ideas, evidence types, and transitions

### Scoring note

Avoid hardcoding a universal max like "75 words." Research supports the general idea that oversized chunks can hurt retrieval, but the safer evaluation principle is:

- penalize **ambiguous**, **bloated**, and **multi-idea** paragraphs
- reward **compact**, **scoped**, and **self-contained** paragraphs ([Hugging Face](https://huggingface.co/papers/2601.14123))

---

## 4. Answer-First Section Openings

### What to check

- Informational H2 sections begin with a direct answer, definition, or takeaway
- The first paragraph under a major heading resolves the question or frames the claim quickly
- Background, nuance, and supporting detail follow after the answer
- Important claims appear early enough to be retrievable without requiring deep scrolling

### Why this matters

LLM retrieval and citation often over-index on early, high-salience text. A recent citation study reported that 44.2% of ChatGPT citations came from the first third of content. That is not a universal law, but it is a strong practical heuristic: burying the answer deep in a section raises retrieval risk. ([Search Engine Land](https://searchengineland.com/chatgpt-citations-content-study-469483))

### Practical rule

For major sections, open with:

1. the answer,
2. the scope,
3. the supporting context.

### Good pattern

Under `What is llms.txt?`, begin with a short explanatory answer before historical background or implementation details.

### Fail signals

- First paragraph is all preamble or throat-clearing
- The actual answer appears only after several setup paragraphs
- The section begins with marketing copy instead of a clear statement

---

## 5. Exact-Match Retrieval + Semantic Retrieval Coverage

### What to check

- The page includes the literal terminology users are likely to search
- The page also includes semantically related phrasing, synonyms, and explanatory framing
- Product names, feature names, technical identifiers, and domain terms are written explicitly
- Important comparisons and category terms are named directly, not only implied

### Why this matters

Modern retrieval is often hybrid. Anthropic describes a standard setup where semantic embeddings retrieve conceptually similar chunks while BM25 helps retrieve exact terms, unique identifiers, and technical strings. Hybrid retrieval generally outperforms semantic-only retrieval. ([Anthropic](https://www.anthropic.com/research/contextual-retrieval))

### Practical rule

Write for both:

- **semantic match**: "AI visibility," "answer engine optimization," "agent-readability"
- **lexical match**: exact product names, comparison terms, schema types, policy filenames, technical phrases

### Fail signals

- The page implies a concept without naming it
- Brand language replaces category language everywhere
- Technical pages omit exact terms users actually query
- Headings and body copy lack retrieval vocabulary diversity

---

## 6. Query Fan-Out & Reasoning Retrieval Support

> **Scope:** This section evaluates per-page structural support for multi-step retrieval — whether a single page decomposes its topic into retrievable sub-sections. This is distinct from Category 4 (Query Fanout, `query-fanout.md`), which evaluates domain-level coverage — whether any page on the site answers a given sub-query. A page can score well here (good decomposition) while the site scores poorly on Category 4 (missing pages for key sub-queries), and vice versa.

### What to check

- Complex topics are decomposed into clear subtopics
- A section answers adjacent questions a system might need during multi-step retrieval
- The page supports follow-on queries such as comparisons, implementation steps, caveats, cost, examples, and edge cases
- Important supporting facts are discoverable without requiring a single perfect query

### Why this matters

Not all retrieval problems are simple keyword lookups. The BRIGHT benchmark shows that state-of-the-art retrievers perform poorly on reasoning-intensive retrieval tasks, and augmenting queries with chain-of-thought style reasoning improved performance by up to 12.2 points. This supports the idea that good AEO/GEO pages should support **query expansion** and **sub-question retrieval**, not only one surface-level match. ([Hugging Face](https://huggingface.co/papers/2407.12883))

### Practical rule

A strong page gives AI systems multiple ways to retrieve the same useful knowledge:

- direct definitions,
- process explanations,
- examples,
- comparisons,
- FAQs,
- edge-case clarifications.

### Fail signals

- Only one phrasing of the core concept appears
- No support for adjacent user questions
- Key nuance exists only in a single hidden paragraph
- Complex topics are presented as one undifferentiated block

---

## 7. Lists, Tables, and Parseable Structure

### What to check

- Sequential processes use numbered lists
- Non-sequential related ideas use bullet lists
- Comparisons use parseable HTML tables where appropriate
- Tables have clear headers and nearby explanatory text
- Structured information is not locked inside images

### Why this matters

Structured blocks are easier to parse, quote, compare, and reuse. They also help preserve local meaning when content is chunked. Comparative content especially benefits from table structure instead of dense prose. ([Google for Developers](https://developers.google.com/search/docs/appearance/ranking-systems-guide))

### Practical rule

Use structure to reduce ambiguity:

- steps → numbered list
- grouped ideas → bullets
- comparisons/specs/pricing → table
- summary facts → compact callout or intro block

### Fail signals

- Processes described only in long prose
- Tables rendered as images
- Merged-cell layouts that are hard to parse
- List items that are effectively whole paragraphs

---

## 8. FAQs as Retrieval Primitives

### What to check

- Informational pages include FAQ-like question-answer units when appropriate
- Questions reflect realistic user phrasing
- Answers are concise, direct, and specific
- FAQ items are semantically marked up with headings or clear structure
- FAQ content adds net-new retrieval coverage rather than repeating fluff

### Why this matters

FAQ structures map naturally to user queries and make strong retrieval units. They are especially useful for capturing adjacent questions, objections, and long-tail phrasing. They also support multi-step retrieval and answer synthesis by making intent boundaries explicit. This is directionally consistent with both passage retrieval and reasoning-retrieval evidence. ([Google for Developers](https://developers.google.com/search/docs/appearance/ranking-systems-guide))

### Fail signals

- No FAQ-like query coverage on informational pages
- Answers are vague or overly long
- Questions are artificial and not aligned with real user intent
- FAQ content is presented as a wall of text

---

## 9. Summaries, TL;DRs, and High-Salience Blocks

### What to check

- Long-form pages surface a summary or high-salience answer block near the top
- The summary can stand on its own as a quotable synthesis
- Key claims, metrics, and category framing appear early
- Introductory blocks are informative, not generic marketing filler

### Why this matters

Early content often receives disproportionate attention in retrieval and citation. The first third of a page appears especially important in recent ChatGPT citation behavior. Again, this should be used as a practical heuristic rather than a universal rule. ([Search Engine Land](https://searchengineland.com/chatgpt-citations-content-study-469483))

### Fail signals

- No summary on long-form informational pages
- The top of the page is all branding with no informational payload
- Important claims are buried deep in the page

---

## 10. Structured Data & Semantic HTML

Structured data and semantic HTML are evaluated under Category 1 (Agentic Readiness) — see `agentic-readiness.md`. They are not scored again here. The only chunking-specific implication: pages with strong semantic HTML are more likely to survive preprocessing and produce coherent chunks. Do not claim that JSON-LD alone solves retrieval.

---

## Scoring Guide

Use this scoring guide to evaluate chunking and retrieval quality.

| Area | Weight | What to Check |
| --- | --- | --- |
| Heading Hierarchy & Retrieval Anchors | 20% | One H1, proper nesting, query-aligned headings, section-defining phrasing |
| Section Scope & Chunk Boundaries | 20% | One major idea per section, clean topic boundaries, nearby supporting context |
| Paragraph Self-Containment | 15% | Compact paragraphs, explicit local context, low ambiguity, one main idea |
| Answer-First Openings | 15% | Direct answer or takeaway appears early under major headings |
| Retrieval Vocabulary Coverage | 10% | Exact-match terminology plus semantic phrasing and related concepts |
| Lists, Tables & Parseable Structure | 10% | Structured formatting where useful, parseable tables, non-image comparisons |
| FAQ / Query Fan-Out Coverage | 5% | Long-tail questions, adjacent intent coverage, reusable Q&A units |
| Top-of-Page Summary / Salience | 5% | Summary or high-signal answer block appears early |

### Scoring interpretation

- **90–100:** Excellent retrieval shape. Strong section boundaries, self-contained answers, high reranking survivability.
- **75–89:** Good retrieval shape. Some sections may be too broad, buried, or weakly phrased.
- **50–74:** Mixed retrieval quality. Important answers exist, but chunking and reranking risk is noticeable.
- **0–49:** Poor retrieval shape. Content is hard to parse into reliable answer units.

---

## Issue ID Pattern

Issue IDs for chunking/retrieval problems should use:

`chunking-{specific-problem}`

Examples:

- `chunking-broken-heading-hierarchy`
- `chunking-generic-headings`
- `chunking-overscoped-section`
- `chunking-weak-local-context`
- `chunking-buried-answer`
- `chunking-missing-query-terms`
- `chunking-prose-instead-of-list`
- `chunking-unparseable-table`
- `chunking-no-faq-coverage`
- `chunking-no-top-summary`
- `chunking-ambiguous-paragraphs`
- `chunking-split-supporting-evidence`

---

## Audit Heuristics

Use these quick tests during evaluation.

### Self-containment test

Can a retrieved paragraph or short section still make sense if shown alone?

### Answer-first test

Does the first paragraph under a major heading resolve the question quickly?

### Retrieval anchor test

Would a heading and its first paragraph match a realistic search or AI query?

### Exact-match test

Does the page explicitly include the literal terms users or systems will search?

### Reranking test

If a system retrieved 20 similar chunks, would this one survive because it is specific, clear, and locally complete?

---

## Key Evaluation Principle

Do not optimize for one rigid chunk size or one cosmetic writing style.

Optimize for **retrieval resilience**:

- sections with clean semantic boundaries,
- paragraphs with enough local context,
- answer-first structure,
- explicit terminology,
- parseable formatting,
- and high odds of surviving reranking.

That is the standard most aligned with how modern passage ranking and retrieval systems actually behave. ([Google for Developers](https://developers.google.com/search/docs/appearance/ranking-systems-guide))

---