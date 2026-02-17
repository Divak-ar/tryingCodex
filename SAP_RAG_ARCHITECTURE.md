# SAP Enterprise RAG Architecture (ABAP + Functional + Support)

## 1) Architecture Explanation

### 1.1 Objectives
- Assist **ABAP developers**, **functional consultants**, and **support teams** with grounded answers.
- Operate with **no direct SAP system access** (air-gapped or export-based mode).
- Use only **approved internal SAP documentation and code exports**.
- Enforce **enterprise governance, security, and auditability**.

### 1.2 High-Level Components
1. **Source Connectors (Offline/Batch)**
   - Input sources: ABAP code exports (`.abap`, `.txt`), DDIC extracts, transport object lists, functional specs (FS), technical specs (TS), OSS note archives, incident runbooks, customizing guides, test evidence, release notes.
   - Connectors read from approved repositories (Git mirrors, secure file drops, DMS exports, SharePoint export, Confluence export, ticketing export).

2. **Ingestion & Normalization Pipeline**
   - Parses source files and converts to canonical JSON documents.
   - Extracts document type, module, application component, release, language, owner, confidentiality, and provenance metadata.
   - Performs PII/secrets detection and optional redaction/tokenization before indexing.

3. **Chunking & Enrichment Engine**
   - Splits content into semantically coherent chunks by object boundaries (ABAP class/method/form/function module), section headings, or process steps.
   - Adds chunk-level metadata and derived entities (transaction codes, table names, BAPI names, message classes, package names, authorization objects).

4. **Storage Layer**
   - **Object Store** for original and normalized documents.
   - **Vector Store** for embeddings.
   - **Metadata/Graph Store** for structured lookup and lineage (document->chunk->source).
   - **Audit Log Store** for immutable request/retrieval/response events.

5. **Retrieval & Reranking Service**
   - Hybrid retrieval = lexical (BM25) + vector similarity + metadata filters.
   - Reranking model prioritizes SAP-specific relevance and recency.
   - Policy gate enforces user entitlements, data classification rules, and jurisdiction constraints.

6. **LLM Orchestration Service**
   - Builds role-specific prompts with retrieved context and citation requirements.
   - Executes confidence checks and contradiction checks.
   - Returns answer with **sources + confidence + unresolved questions**.

7. **User Interfaces**
   - ABAP dev assistant (IDE plugin/web UI), consultant assistant (process Q&A), support assistant (incident copilot).
   - Exposes “show supporting passages” and “why this answer” transparency panel.

### 1.3 Deployment Pattern (Local-First + Enterprise Scale)
- **Local runtime option (developer laptop / jump host):**
  - Ollama-hosted local embedding + local LLM for non-sensitive experimentation.
  - Local encrypted vector DB (e.g., Qdrant/Chroma) with project scope.
- **Enterprise runtime option (on-prem/private cloud):**
  - Centralized ingestion jobs, hardened API gateway, managed vector DB, SIEM integration.
- **No direct SAP read/write path in either mode**; only approved exports enter the platform.

---

## 2) Data Model and Metadata

### 2.1 Canonical Document Schema
```json
{
  "doc_id": "UUID",
  "source_system": "git_export|dms|ticket_export",
  "source_uri": "path/or/url",
  "doc_type": "abap_class|function_module|fs|ts|oss_note|runbook",
  "title": "ZCL_SD_PRICING_HELPER",
  "language": "EN",
  "sap_release": "S4HANA_2022",
  "module": "SD",
  "app_component": "SD-BF-PR",
  "transport": ["K900123"],
  "package": "ZSD_CORE",
  "author": "team_alias",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "classification": "internal|confidential|restricted",
  "retention_policy": "7y",
  "hash_sha256": "...",
  "content": "normalized full text"
}
```

### 2.2 Chunk Schema
```json
{
  "chunk_id": "UUID",
  "doc_id": "UUID",
  "chunk_index": 12,
  "chunk_type": "method|paragraph|procedure_step|qa_pair",
  "start_offset": 1420,
  "end_offset": 1980,
  "content": "...",
  "tokens": 280,
  "entities": {
    "tcode": ["VA01"],
    "table": ["VBAK", "VBAP"],
    "bapi": ["BAPI_SALESORDER_CREATEFROMDAT2"],
    "message_class": ["V1"],
    "auth_object": ["V_VBAK_AAT"]
  },
  "metadata": {
    "sap_release": "S4HANA_2022",
    "module": "SD",
    "country": "GLOBAL",
    "language": "EN",
    "classification": "confidential",
    "owner_team": "ERP_SD_DEV",
    "quality_score": 0.89,
    "effective_from": "2024-01-01",
    "effective_to": null
  },
  "embedding_model": "text-embedding-004",
  "embedding_vector": [0.0123, -0.9921]
}
```

### 2.3 Minimum Metadata Required for Governance
- Provenance: `source_uri`, hash, ingestion timestamp, parser version.
- Authorization attributes: data classification, owning team, jurisdiction.
- Lifecycle attributes: effective dates, superseded-by link, retention policy.
- Semantic SAP tags: module, app component, object type, release level.

---

## 3) Ingestion and Chunking Design

### 3.1 Ingestion Workflow
1. **Acquire exports** from approved internal systems.
2. **Validate** checksums and signature (if provided).
3. **Normalize** formats (PDF/Docx/ABAP sources to text + structure).
4. **Classify and label** by SAP domain and security class.
5. **Detect sensitive data** (credentials, personal data, production IDs).
6. **Redact/tokenize** where policy requires.
7. **Chunk and enrich** with entities + metadata.
8. **Embed + index** in vector and lexical indexes.
9. **Record lineage** in audit metadata store.

### 3.2 Chunking Strategy (SAP-Specific)
- ABAP objects:
  - Prefer chunks per method/form/function include; include nearby signature/comments.
  - Keep method body coherent (target 200–500 tokens; hard cap ~800).
- Functional docs:
  - Chunk by process step, exception flow, configuration path (IMG node).
- Support runbooks/incidents:
  - Chunk by symptom, root cause, resolution, rollback, validation.
- Overlap:
  - 10–15% overlap to preserve context around boundary conditions.

### 3.3 Quality Controls
- Reject chunks with low signal (boilerplate-only).
- Deduplicate via MinHash/SimHash across near-identical transports.
- Mark stale chunks when newer release supersedes prior guidance.

---

## 4) Retrieval Logic

### 4.1 Query Understanding
- Detect role intent: `ABAP_DEV`, `FUNCTIONAL`, `SUPPORT`.
- Extract SAP entities from query (TCode, table, class, message number, plant/company code).
- Determine answer mode: explanation, troubleshooting, code suggestion, process impact.

### 4.2 Retrieval Pipeline
1. **Policy pre-filter** by user entitlement + classification + geography.
2. **Metadata filter** by module/release/language if inferable.
3. **Hybrid retrieve**:
   - BM25 top-K lexical
   - Vector top-K semantic
4. **Fusion** with reciprocal rank fusion (RRF).
5. **Cross-encoder rerank** for final top-N passages.
6. **Coverage check**:
   - Must include at least one high-authority source (spec/runbook/code owner doc) when available.
7. **Context pack assembly** with citations and relevance scores.

### 4.3 Anti-Hallucination Guardrails
- Answer only from retrieved context; if insufficient, say “insufficient evidence”.
- Force citation for each material claim.
- Add “conflict detector” if retrieved passages disagree.
- Add “release mismatch detector” if query release differs from source release.
- For ABAP code generation:
  - enforce non-executable draft label,
  - require user validation checklist (syntax check, ATC, unit tests, security checks).

---

## 5) Prompt Design Templates

### 5.1 System Prompt (Global)
```
You are an SAP enterprise assistant. You must only use the provided context.
If evidence is insufficient or conflicting, explicitly say so.
Cite source IDs for every key claim.
Never invent SAP tables, BAPIs, tcodes, OSS notes, or configuration steps.
Prioritize latest valid release-matching sources.
Output sections: Answer, Evidence, Risks/Assumptions, Validation Steps.
```

### 5.2 ABAP Developer Prompt Template
```
Role: ABAP developer assistant
Task: {{question}}
System context: SAP release={{release}}, module={{module}}
Constraints:
- Use only retrieved context.
- If proposing code, provide pseudocode or draft ABAP with explicit assumptions.
- Include ATC/security/performance checklist.

Retrieved context:
{{ranked_chunks_with_source_ids}}
```

### 5.3 Functional Consultant Prompt Template
```
Role: Functional consultant assistant
Task: {{question}}
Focus: process impact, customizing dependencies, integration touchpoints
Constraints:
- State whether answer is release-specific.
- Highlight org/process prerequisites.
- Provide validation steps in QA system.

Retrieved context:
{{ranked_chunks_with_source_ids}}
```

### 5.4 Support Team Prompt Template
```
Role: SAP support incident copilot
Task: {{incident_question}}
Constraints:
- Structure as: Symptom -> Likely Causes -> Diagnostic Steps -> Resolution -> Rollback.
- Mention production-safety warnings.
- If evidence weak, recommend escalation path.

Retrieved context:
{{ranked_chunks_with_source_ids}}
```

---

## 6) Model Options (Local + Cloud)

### 6.1 Primary Requirement
- Support **Gemini API or Ollama** as requested.

### 6.2 Recommended Model Matrix
- **Cloud (1–2 options)**
  1. Gemini 1.5 Pro / 2.0 family (generation + long context).
  2. Azure OpenAI GPT-4.1 (enterprise controls, private networking).
- **Local (1–2 options)**
  1. Llama 3.1/3.2 Instruct via Ollama (on-prem inference).
  2. Mistral 7B/8x7B variant via Ollama (cost-efficient local fallback).

### 6.3 Embeddings
- Cloud: `text-embedding-004` (Gemini stack) where policy allows.
- Local: `bge-large` / `nomic-embed-text` via Ollama-compatible serving.

### 6.4 Suggested Runtime Structure
- Pluggable provider interface:
  - `EmbeddingProvider`: cloud/local selectable.
  - `LLMProvider`: gemini|ollama|azure-openai.
  - `RerankerProvider`: local cross-encoder fallback if cloud unavailable.
- Store context locally in vector DB with periodic signed snapshot backups.

---

## 7) Governance, Security, and Audit

### 7.1 Governance Controls
- Data steward approval before adding new source domains.
- Mandatory source catalog with owner + classification + retention.
- Model risk management: documented intended use, prohibited use, periodic review.

### 7.2 Security Controls
- SSO + RBAC/ABAC (role + project + geography).
- Encryption at rest (KMS-managed keys) and in transit (TLS 1.2+).
- Secret isolation in vault; no credentials in prompts/index.
- Red-team tests for prompt injection from poisoned docs.

### 7.3 Audit & Compliance
- Immutable logs for:
  - user query,
  - retrieved chunk IDs,
  - prompt version,
  - model/version,
  - response,
  - user feedback/override.
- Retain logs per compliance policy and legal hold workflows.
- Support evidence export for audits (SOX, ISO 27001, GDPR-style controls).

---

## 8) Failure Cases and Fixes

1. **Hallucinated SAP object names**
   - Fix: strict citation enforcement + entity whitelist validator + abstain policy.

2. **Outdated release guidance**
   - Fix: release-aware filtering; downrank stale docs; explicit “applies to release X”.

3. **Conflicting runbooks/specs**
   - Fix: conflict detector + show both sources + escalate to owner.

4. **Permission leakage across teams**
   - Fix: retrieval-time policy filter + encrypted tenant partitions + row-level ACL tests.

5. **Prompt injection in documentation**
   - Fix: sanitize retrieved text, strip instruction-like segments, maintain immutable system prompt hierarchy.

6. **Low retrieval recall for custom Z* objects**
   - Fix: SAP-aware tokenization, synonym dictionaries, package/object metadata boosts.

---

## 9) Production Hardening Guidelines

1. **Reliability**
   - Queue-based ingestion with retry + dead-letter queue.
   - Blue/green model deployment and rollback.
   - Circuit breakers for external model APIs.

2. **Performance**
   - Cache frequent query embeddings.
   - Two-stage retrieval (fast coarse, slower rerank).
   - Precompute entity indexes for tables/tcodes/program IDs.

3. **Quality Monitoring**
   - Golden question set per SAP module (FI, CO, SD, MM, PP, HCM).
   - Metrics: groundedness, citation coverage, answer usefulness, abstention quality.
   - Human review loop with correction capture and re-index triggers.

4. **Change Management**
   - Version prompts, chunkers, and parsers.
   - Track index generation IDs for reproducibility.
   - CAB-style approval for production policy changes.

5. **Operational Runbook**
   - Incident severity model for incorrect guidance.
   - “Kill switch” to disable high-risk answer modes (e.g., auto-code suggestions).
   - Mandatory disclaimer: recommendations require SAP QA validation before production use.

---

## 10) Minimal Implementation Blueprint (Local to Enterprise)

1. Start local PoC:
   - Ollama + local embedding + local vector DB + file-based ingestion.
2. Add enterprise controls:
   - SSO, RBAC, data classification, audit logging, policy engine.
3. Add hybrid model routing:
   - default local; cloud escalation for complex long-context queries where allowed.
4. Add continuous learning loop:
   - capture accepted answers, rejected answers, and expert corrections as new governed knowledge assets.

This design keeps SAP knowledge grounded in approved internal artifacts, avoids direct SAP connectivity, and prioritizes compliance-grade traceability.
