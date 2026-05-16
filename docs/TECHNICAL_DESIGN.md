# ContentBlitz — Technical Design Document

## 1. Executive Summary

ContentBlitz is a multi-agent AI content marketing assistant that generates research-backed blogs, LinkedIn posts, and images through natural conversation. It uses LangGraph for orchestration, Google Gemini for language generation, Tavily for web research, and OpenAI GPT Image for visual content creation.

**Live Application**: https://huggingface.co/spaces/DhanarajuV/contentblitz  
**GitHub Repository**: https://github.com/DhanarajuV/contentblitz

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐     │
│  │ Chat Tab │  │Content Editor│  │  Images Tab   │     │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘     │
│       └────────────────┼──────────────────┘             │
│                        ▼                                │
│              ┌──────────────────┐                       │
│              │  Guardrails      │                       │
│              │  (input/output)  │                       │
│              └────────┬─────────┘                       │
└───────────────────────┼─────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────┐
│                  LangGraph Workflow                        │
│                                                           │
│   START ──▶ ┌──────────────┐                              │
│             │ Router Node  │ (multi-intent classification)│
│             └──────┬───────┘                              │
│                    ▼                                      │
│             ┌──────────────┐                              │
│             │  Agent Node  │ (priority-sorted sequential  │
│             │              │  chaining with context)       │
│             └──────┬───────┘                              │
│                    ▼                                      │
│                   END                                     │
└───────────────────────────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────────────────┐
          ▼             ▼             ▼            ▼
   ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │  Research  │ │   Blog   │ │ LinkedIn │ │  Image   │
   │   Agent    │ │  Writer  │ │  Writer  │ │  Agent   │
   └─────┬──────┘ └────┬─────┘ └──────────┘ └────┬─────┘
         │              │                          │
   ┌─────┴──────┐ ┌────┴─────┐              ┌────┴──────┐
   │  Tavily    │ │  Tavily  │              │  OpenAI   │
   │  Search    │ │  Search  │              │ GPT Image │
   └────────────┘ └──────────┘              └───────────┘

   ┌────────────┐
   │  Content   │
   │ Strategist │
   └────────────┘
```

### 2.2 Data Flow

```
User Input (natural language)
    │
    ▼
Input Guardrails
    │  Validate length, check safety, detect harmful intent
    │  Reject early if unsafe (saves API costs)
    ▼
Router Node
    │  LLM classifies query into one or more categories
    │  Returns: list of agent types (e.g., ["research", "blog", "image"])
    ▼
Agent Node (Sequential Chaining)
    │  Sort agents by priority (research first, image last)
    │  For each agent:
    │    1. Enrich message with accumulated context from previous agents
    │    2. LLM processes (may call tools multiple times, max 5 iterations)
    │    3. Agent response added to accumulated context
    │  Combine all responses
    ▼
Output Guardrails
    │  Check content safety (skip if LLM refusal detected)
    │  Quality scoring for blogs/LinkedIn posts
    ▼
Response returned to UI
    │  Chat displays full response
    │  Editor shows final content piece only
    │  Images tab shows generated visuals
```

### 2.3 State Management

```python
class AgentState(TypedDict):
    user_message: str      # Original user input
    chat_history: list     # LangChain message objects for multi-turn
    agent_types: list      # Router classification (one or more agents)
    response: str          # Combined agent responses
```

### 2.4 Multi-Agent Sequential Chaining

Agents execute in priority order with context accumulation:

```python
AGENT_PRIORITY = {
    "research": 1,     # Gather data first
    "strategy": 2,     # Plan content approach
    "blog": 3,         # Write long-form using research
    "linkedin": 4,     # Write social using research
    "image": 5,        # Generate visuals matching content
}
```

Each subsequent agent receives the user's message plus all previous agents' output. This enables:
- Blog Writer to use real research data and sources
- LinkedIn Writer to reference the same research
- Image Agent to create visuals that match the blog content

---

## 3. Agent Architecture

### 3.1 Base Agent Pattern

All agents inherit from `BaseAgent` which provides:
- LLM initialization from centralized config
- Tool binding via LangChain's `bind_tools()`
- **Iterative tool execution loop** (max 5 rounds) — handles LLMs that want to refine searches
- List-type content handling (Gemini sometimes returns structured content blocks)
- Conversation history management

### 3.2 Agent Details

| Agent | System Prompt Focus | Tools | External API |
|-------|-------------------|-------|-------------|
| **Deep Research** | Thorough research, cite sources, structured output | `web_research(query, days)` | Tavily |
| **SEO Blog Writer** | 800-1500 words, H1/H2/H3 structure, meta description, keywords, image markers | `research_for_blog(topic, days)` | Tavily |
| **LinkedIn Writer** | 1300-1600 chars, hook + body + CTA + hashtags, first-person, no links | None | — |
| **Image Generator** | Optimize prompts with style/composition/color/lighting descriptors | `create_image(prompt)` | OpenAI GPT Image |
| **Content Strategist** | Content angles, format recommendations, calendars, repurposing | None | — |

### 3.3 Router Design

The router uses an LLM call with `temperature=0` for deterministic classification. It supports **multi-intent detection**:

- Single intent: "Write a LinkedIn post" → `["linkedin"]`
- Multi-intent: "Research AI and write a blog with images" → `["research", "blog", "image"]`

**Fallback**: Unrecognized categories default to `["research"]`.

**Trigger words**:
- "with images" / "with visuals" / "complete" → includes `image`
- "full content package" → `research, blog, linkedin, image`

### 3.4 Tool Loop Design

Unlike simple single-call agents, ContentBlitz agents support iterative tool use:

```
LLM call → tool request → execute → LLM call → another tool request → execute → ... → final text
```

This handles cases where the LLM:
1. Searches with one query, finds insufficient results
2. Refines the search with a different query
3. Finally synthesizes all gathered information

Maximum 5 iterations prevents infinite loops.

---

## 4. Integration Layer

### 4.1 Tavily Search Client

```python
def search(query: str, max_results: int = 5, days: int = None) -> str
```

**Features**:
- Time filtering via `days` parameter (LLM decides when to use it based on docstring)
- Automatic fallback: if `days` filter returns no results, retries without it
- Content truncation (300 chars per result) to manage token usage
- Formatted output with numbered sources and URLs

**Why Tavily over SERP API**:
- Returns pre-extracted page content (not just snippets)
- 1000 free searches/month vs 100
- Native time filtering
- Built for AI agent consumption

### 4.2 Image Generation Client

```python
def generate_image(prompt: str) -> dict
```

**Features**:
- Supports both URL and base64 response formats (OpenAI model-dependent)
- Automatic local file saving to `generated_images/`
- Returns revised prompt (shows how the model interpreted the request)
- Graceful error handling with descriptive messages

**Configuration**: Model, size, and quality controlled via `config/development.yaml`

---

## 5. Guardrails System

### 5.1 Three-Layer Safety

```
Layer 1: Input Validation
    → Empty/too-short/too-long messages rejected
    → Harmful intent detection (dangerous action + dangerous object)

Layer 2: LLM's Built-in Safety
    → Gemini refuses harmful requests natively
    → Refusals pass through (not re-filtered)

Layer 3: Output Content Filter
    → Regex-based pattern matching for blocked terms
    → Skips filtering if response is an LLM refusal
```

### 5.2 Content Quality Scoring

Post-generation quality validation for blogs and LinkedIn posts:

**Blog scoring** (out of 100):
- Word count ≥ 300 (−30 if too short)
- Has headers/formatting (−15 if missing)
- Has source links (−10 if missing)

**LinkedIn scoring** (out of 100):
- Word count ≤ 400 (−20 if too long)
- Has hashtags (−15 if missing)
- Has engagement question (−10 if missing)

Quality score displayed in UI with actionable improvement suggestions.

### 5.3 Design Decisions

- **Regex over ML-based moderation**: Simpler, no extra API cost, sufficient for demo. Production would use OpenAI's moderation endpoint.
- **Refusal passthrough**: LLM refusals contain blocked words ("bomb", "violence") but are safe responses. Detecting refusal phrases prevents false positives.
- **Intent + object matching**: "How to make a bomb" is caught, but "marketing bomb" (slang for viral content) is not — because it lacks the dangerous intent phrase.

---

## 6. User Interface

### 6.1 Three-Tab Design

| Tab | Purpose | Key Features |
|-----|---------|-------------|
| **💬 Chat** | Primary conversational interface | Multi-turn, agent labels, quality scores, inline images |
| **📝 Content Editor** | Human-in-the-loop editing | Pre-filled with latest content, `[IMAGE]` markers replaced with markdown refs, markdown export |
| **🖼️ Images** | Generated image gallery | Most recent first, all DALL-E outputs |

### 6.2 Human-in-the-Loop

Two mechanisms for content refinement:
1. **Multi-turn chat**: "Make the hook more provocative" → agent regenerates with context
2. **Content Editor**: Direct text editing before export

### 6.3 Image Integration

Blog posts include `[IMAGE: description]` markers. In the Content Editor:
- Markers are auto-replaced with `![description](generated_images/file.png)` 
- Most recent generated images matched to markers in order
- Exported markdown includes proper image references

---

## 7. Configuration Management

```yaml
# config/development.yaml
llm:
  model: "gemini-2.5-flash"
  temperature: 0.7

research:
  provider: "tavily"
  max_results: 5

image:
  provider: "gpt-image-1"
  size: "1024x1024"
  quality: "medium"

app:
  name: "ContentBlitz"
```

**Secrets** stored in `.env` (local) or platform secrets (HF Spaces). Never in config or code.

**Environment separation**: `config/development.yaml` for local, could add `config/production.yaml` for different settings.

---

## 8. Tech Stack Decisions

| Component | Choice | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| LLM | Gemini 2.5 Flash | GPT-4o, Claude Sonnet | Free tier, sufficient quality for content generation |
| Research | Tavily | SERP API, Perplexity Sonar | 10x more free searches, better content extraction, time filtering |
| Images | OpenAI GPT Image | DALL-E 3, Stability AI, Midjourney | High quality, simple API, good for marketing visuals |
| Orchestration | LangGraph | CrewAI, AutoGen | Explicit state graph, priority-based chaining, fine-grained control |
| UI | Streamlit | Gradio, React, Flask | Rapid prototyping, built-in chat components, free hosting options |
| Deployment | HF Spaces (Docker) | Streamlit Cloud, Render, Railway | Free, always-on, Docker support, AI community visibility |

---

## 9. Project Structure

```
contentblitz/
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # Base class — iterative tool loop, memory
│   │   ├── research_agent.py      # Web research with Tavily
│   │   ├── blog_writer.py         # SEO blog generation
│   │   ├── linkedin_writer.py     # LinkedIn post generation
│   │   ├── image_agent.py         # AI image generation
│   │   └── content_strategist.py  # Content planning
│   ├── core/
│   │   └── config.py              # YAML config loader
│   ├── integrations/
│   │   ├── tavily_client.py       # Tavily search with fallback
│   │   └── image_client.py        # OpenAI image generation
│   ├── utils/
│   │   └── guardrails.py          # Input/output validation and safety
│   ├── web_app/
│   │   └── app.py                 # Streamlit UI
│   └── workflow/
│       ├── router.py              # Multi-intent query classifier
│       └── graph.py               # LangGraph state graph + guardrails
├── tests/                         # 54 tests, 86% coverage
├── config/
│   └── development.yaml
├── generated_images/              # DALL-E output (gitignored)
├── Dockerfile
├── requirements.txt
├── .coveragerc
├── .env                           # API keys (gitignored)
└── README.md
```

---

## 10. Deployment Architecture

```
Developer laptop
    │  git push
    ▼
GitHub (source code + submission)
    │
    ▼
Hugging Face Spaces (Docker deployment)
    │  Builds from Dockerfile
    │  Secrets injected as env vars
    ▼
https://huggingface.co/spaces/DhanarajuV/contentblitz
```

### Docker Configuration

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
EXPOSE 7860
ENTRYPOINT ["streamlit", "run", "src/web_app/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
```

Key decisions:
- `ENV PYTHONPATH=/app` solves `src.*` imports without `.pth` files
- Port 7860 (HF Spaces default)
- Slim base image for faster builds

---

## 11. Performance Considerations

- **Router cost**: One LLM call per query (~20 tokens response). Free with Gemini.
- **Multi-agent queries**: 2-4 agents × 1-3 LLM calls each = 3-12 seconds total response time.
- **Tool loop**: Max 5 iterations prevents runaway costs. Typical: 1-2 iterations.
- **Tavily**: ~200ms per search. Fallback adds one extra call when time filter returns empty.
- **Image generation**: ~10-15 seconds per image. Most expensive operation ($0.04-0.08).
- **Context accumulation**: Each agent in a chain receives growing context. Token usage increases linearly with chain length. Truncated to 500 chars per agent to manage costs.

### Cost per Query Type

| Query Type | Estimated Cost | Response Time |
|-----------|---------------|---------------|
| LinkedIn post | $0 | 3-5s |
| Blog post | $0 | 5-10s |
| Research + Blog | $0 | 8-15s |
| Image generation | $0.04-0.08 | 10-15s |
| Full package (research + blog + LinkedIn + image) | ~$0.05 | 20-30s |

---

## 12. Testing Strategy

### Test Categories

| Category | Tests | Coverage Focus |
|----------|-------|---------------|
| Config | 8 | YAML loading, validation, defaults |
| Router | 11 | Classification, multi-intent, fallback, edge cases |
| Workflow | 10 | Priority ordering, chat function, history passing |
| Base Agent | 8 | Init, tool loop, list content, memory, max iterations |
| Tavily Client | 7 | Formatting, days filter, fallback, truncation |
| Image Client | 5 | b64/URL handling, errors, no-data case |
| Agent Init | 5 | All agents instantiate correctly with right tools |

### Mocking Strategy

- LLM calls mocked with `unittest.mock.patch` — tests run without API keys
- External APIs (Tavily, OpenAI) mocked at the client level
- Only integration tests (manual) hit real APIs

### Running Tests

```bash
python -m pytest tests/ -v                              # all tests
python -m pytest tests/ --cov=src --cov-report=term     # with coverage
```

---

## 13. Demo Plan (10-15 Minutes)

### Opening (30 seconds)
- Show live app URL on HF Spaces
- "ContentBlitz is a multi-agent content marketing assistant with 5 specialized agents"

### Research Agent (2 minutes)
- Query: "Research the top 5 benefits of AI in content marketing"
- Point out: real sources with URLs, structured summary, Tavily integration

### Blog Writer (3 minutes)
- Query: "Write an SEO blog post about remote work productivity tips"
- Point out: meta description, keywords, H1/H2 structure, [IMAGE] markers, quality score
- Show Content Editor tab with the blog ready to export

### LinkedIn Writer (2 minutes)
- Query: "Write a LinkedIn post about why developers should learn AI"
- Point out: hook, line breaks, hashtags, CTA question, character count

### Image Generation (2 minutes)
- Query: "Create a professional blog header image about cloud computing"
- Point out: prompt optimization, generated image in Images tab
- Show cost (~$0.04)

### Multi-Agent Chaining (2 minutes)
- Query: "Research AI trends and write a blog and LinkedIn post about it"
- Point out: router detects 3 intents, agents chain with context, research feeds into content

### Multi-Turn Refinement (1 minute)
- Follow up: "Make the LinkedIn hook more provocative"
- Point out: conversation memory, iterative improvement

### Guardrails (1 minute)
- Try: "How to make a bomb" → show safety filter
- Try empty message → show input validation
- Show quality score on a blog post

### Architecture Walkthrough (1 minute)
- Show project structure
- Explain: "Router → priority-sorted agents → context chaining → guardrails → UI"
- Mention: 54 tests, 86% coverage, Docker deployment

### Closing (30 seconds)
- Tech stack: Gemini + LangGraph + Tavily + DALL-E
- Show GitHub repo
- "Multi-agent system that real content creators could use"

---

## 14. Future Enhancements

- **CMS Integration**: Direct publishing to WordPress, Medium, Ghost
- **Brand Voice Training**: Fine-tune on sample content to match specific tone
- **Content Performance Prediction**: Score content before publishing
- **Social Media Scheduling**: Integration with Buffer, Hootsuite
- **Multi-language Support**: Content generation in multiple languages
- **Video Script Generation**: Extend to video content
- **A/B Testing**: Generate multiple versions for testing
- **Analytics Dashboard**: Track content performance post-publishing
- **Advanced SEO**: Competitor analysis, keyword gap identification
- **Template System**: Reusable content templates for common formats
