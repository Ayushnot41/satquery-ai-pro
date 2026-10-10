# Graph Report - Satquery Ai  (2026-09-07)

## Corpus Check
- 71 files · ~42,800 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 605 nodes · 1412 edges · 32 communities (21 shown, 10 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 173 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Subsystem 0
- Subsystem 1
- Subsystem 2
- Subsystem 3
- Subsystem 4
- Subsystem 5
- Subsystem 6
- Subsystem 7
- Agent Orchestration & Dispatch
- Subsystem 9
- Subsystem 10
- Subsystem 11
- Subsystem 12
- Subsystem 13
- Subsystem 14
- Subsystem 15
- Subsystem 16
- Subsystem 17
- Subsystem 18
- Subsystem 19
- Subsystem 20
- Subsystem 21
- Subsystem 22
- Subsystem 23
- Subsystem 24
- Subsystem 25
- Subsystem 26
- Subsystem 27
- Subsystem 28
- Subsystem 29
- Subsystem 30

## God Nodes (most connected - your core abstractions)
1. `ExecutionTrace` - 56 edges
2. `AgentBase` - 31 edges
3. `InvestigationOrchestrator` - 31 edges
4. `ImageryInput` - 23 edges
5. `VLMBackend` - 23 edges
6. `TraceEvent` - 22 edges
7. `EvidenceFusionAgent` - 22 edges
8. `SensorType` - 20 edges
9. `InvestigationResponse` - 20 edges
10. `SensorRouterAgent` - 19 edges

## Surprising Connections (you probably didn't know these)
- `SensorType` --uses--> `_get_or_create_demo_image()`  [INFERRED]
  backend/app/schemas/imagery.py → backend/app/api/investigation.py
- `SensorType` --uses--> `SensorRouterAgent`  [INFERRED]
  backend/app/schemas/imagery.py → backend/app/agents/sensor_router.py
- `SensorType` --uses--> `_build_imagery()`  [INFERRED]
  backend/app/schemas/imagery.py → backend/app/api/v1.py
- `ImageryMetadata` --uses--> `get_imagery_metadata()`  [INFERRED]
  backend/app/schemas/imagery.py → backend/app/api/imagery.py
- `ImageryMetadata` --uses--> `list_all_imagery()`  [INFERRED]
  backend/app/schemas/imagery.py → backend/app/api/imagery.py

## Import Cycles
- None detected.

## Communities (32 total, 10 thin omitted)

### Community 0 - "Subsystem 0"
Cohesion: 0.05
Nodes (69): asyncio, AuditTraceAgent, Agent 9: Create an observable record of the investigation. This agent is…, Finalize and validate the execution trace., Validate trace integrity., Generate a human-readable summary of the investigation trace., ChangeDetectionAgent, Agent 5: Detect and interpret meaningful changes between temporal images. Uses… (+61 more)

### Community 1 - "Subsystem 1"
Cohesion: 0.06
Nodes (64): ExecutionTrace, Agent 8: Confidence & Uncertainty — Estimates reliability from measurable…, Determine confidence level from evidence., Generate human-readable confidence explanation., Assess confidence based on available evidence., EvidenceFusionAgent, ExecutionTrace, FusedEvidence (+56 more)

### Community 2 - "Subsystem 2"
Cohesion: 0.06
Nodes (57): _get_or_create_demo_image(), Path, Generate or retrieve a verified demo image file on disk., _build_imagery(), cancel_investigation(), create_investigation(), create_scene(), evaluation_runs() (+49 more)

### Community 3 - "Subsystem 3"
Cohesion: 0.07
Nodes (43): Home(), Header(), HeaderProps, EvaluationView(), InvestigationWorkspace(), InvestigationWorkspaceProps, MissionHome(), MissionHomeProps (+35 more)

### Community 4 - "Subsystem 4"
Cohesion: 0.08
Nodes (32): Agent 9: Audit & Trace — Creates observable execution records., AgentBase, ABC, Any, Base agent class — all nine BHUVISION agents inherit from this., Base class for all BHUVISION agentic components. Each agent: - Has a unique ID…, Record agent start in the trace and return start time., Record agent completion in the trace. (+24 more)

### Community 5 - "Subsystem 5"
Cohesion: 0.06
Nodes (30): argparse, apply_lee_filter(), calibrate_to_db(), ndarray, Synthetic Aperture Radar (SAR) Intelligence Module. Performs scientifically…, Structured scientific evidence produced from SAR imagery., Lee filter for multiplicative SAR speckle noise reduction. Preserves structural…, Convert digital numbers or linear amplitude to radar backscatter in decibels… (+22 more)

### Community 6 - "Subsystem 6"
Cohesion: 0.10
Nodes (19): ChangeRegion, ChangeResult, ndarray, Resize images to the same dimensions., Convert to grayscale if RGB., Apply morphological operations to clean noise., Extract change regions from binary mask using connected components., Generate human-readable change summary. (+11 more)

### Community 7 - "Subsystem 7"
Cohesion: 0.12
Nodes (22): get_imagery_metadata(), list_all_imagery(), get, post, Imagery management and upload endpoints., Upload a satellite image (GeoTIFF, JP2, PNG, JPEG) and parse geospatial…, Retrieve metadata for an uploaded or cached satellite image., List all registered imagery in the workspace. (+14 more)

### Community 8 - "Agent Orchestration & Dispatch"
Cohesion: 0.16
Nodes (17): AuditTrace, BigEarthNet_Pipeline, ChangeDetection, ConfidenceAgent, EvidenceFusion, FastAPI_Main, FreeLLMAPI_Gateway, InputValidation (+9 more)

### Community 9 - "Subsystem 9"
Cohesion: 0.18
Nodes (9): GatewayBackend, ndarray, Generate a caption for satellite imagery., Analyze temporal change. Sends both images side-by-side., Check gateway connectivity., Vision-Language Model serving via FreeLLMAPI or OmniRoute gateway. Uses the…, Lazy-init the OpenAI async client., Convert numpy array to base64-encoded PNG. (+1 more)

### Community 10 - "Subsystem 10"
Cohesion: 0.15
Nodes (9): ABC, ndarray, Abstract interface for vision-language model serving. All model backends (vLLM,…, Answer a question about an image., Generate a caption for an image., Analyze changes between two temporal images., Check if the model backend is healthy and ready., Human-readable name of this backend. (+1 more)

### Community 11 - "Subsystem 11"
Cohesion: 0.18
Nodes (12): Configure structured logging., setup_logging(), get_root(), lifespan(), get, BHUVISION FastAPI Backend Application Entrypoint. SIH26167: SatQuery AI -…, Application startup and shutdown hooks., System banner and metadata. (+4 more)

### Community 12 - "Subsystem 12"
Cohesion: 0.24
Nodes (8): Abstract VLM interface — all model backends must implement this., Deterministic demo backend — pre-computed responses for curated scenarios. This…, AI Gateway backend — routes VLM requests through FreeLLMAPI or OmniRoute., Model serving layer — abstract VLM interface + backends., base64, io, numpy, time

### Community 13 - "Subsystem 13"
Cohesion: 0.27
Nodes (6): Response from a vision-language model., VLMResponse, DemoBackend, ndarray, Deterministic demo backend with pre-computed responses., Detect which demo scenario matches the question.

### Community 14 - "Subsystem 14"
Cohesion: 0.22
Nodes (10): get_investigation(), get_vlm_backend(), list_investigations(), get, Investigation API — Handles agentic Earth intelligence queries., Retrieve the full result, evidence, and audit trace for an investigation., List all previous investigations., get_vlm_backend() (+2 more)

### Community 15 - "Subsystem 15"
Cohesion: 0.22
Nodes (6): Application configuration — reads from environment and .env file., Provider selection is centralized so agent code stays provider-independent., Local vLLM adapter behind the same provider interface as external gateways., OpenAI-compatible adapter for a local vLLM server. It deliberately reuses the…, VLLMBackend, pydantic_settings

### Community 16 - "Subsystem 16"
Cohesion: 0.22
Nodes (9): get_health(), get, Health check endpoint for BHUVISION system status., Retrieve system health status, model serving status, and agent readiness., AgentStatusUpdate, HealthResponse, BaseModel, Health check response. (+1 more)

### Community 17 - "Subsystem 17"
Cohesion: 0.31
Nodes (8): get_scenario(), list_scenarios(), get, Curated demo scenarios for BHUVISION hackathon presentation., List all available curated demo scenarios., Get scenario details by ID., DemoScenario, A pre-configured demo scenario with known outputs.

### Community 18 - "Subsystem 18"
Cohesion: 0.25
Nodes (4): Path, BHUVISION application settings., Settings, BaseSettings

### Community 19 - "Subsystem 19"
Cohesion: 0.29
Nodes (5): get_logger(), Structured logging for BHUVISION., BoundLogger, logging, structlog

### Community 22 - "Subsystem 22"
Cohesion: 0.40
Nodes (3): frontend_src_app_globals, metadata, ref_next

## Knowledge Gaps
- **18 isolated node(s):** `ManifestEntry`, `metadata`, `TaskType`, `SensorDecisionType`, `ConfidenceLevel` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 277 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ExecutionTrace` connect `Subsystem 0` to `Subsystem 1`, `Subsystem 2`, `Subsystem 4`, `Subsystem 6`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `VLMBackend` connect `Subsystem 10` to `Subsystem 0`, `Subsystem 1`, `Subsystem 4`, `Subsystem 9`, `Subsystem 12`, `Subsystem 13`, `Subsystem 14`, `Subsystem 15`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `InvestigationOrchestrator` connect `Subsystem 0` to `Subsystem 1`, `Subsystem 2`, `Subsystem 4`, `Subsystem 6`, `Subsystem 10`, `Subsystem 14`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `ExecutionTrace` (e.g. with `InvestigationResponse` and `AgentBase`) actually correct?**
  _`ExecutionTrace` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AgentBase` (e.g. with `QueryPlannerAgent` and `InputValidationAgent`) actually correct?**
  _`AgentBase` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `InvestigationOrchestrator` (e.g. with `_run_record()` and `SARProcessor`) actually correct?**
  _`InvestigationOrchestrator` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ImageryInput` (e.g. with `_build_imagery()` and `_legacy_request()`) actually correct?**
  _`ImageryInput` has 10 INFERRED edges - model-reasoned connections that need verification._