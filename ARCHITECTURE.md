# BHUVISION System Architecture
### Agentic Earth Intelligence for Government (SIH26167)

---

## 1. System Overview & Design Philosophy

BHUVISION is engineered to solve a fundamental dilemma in remote-sensing AI:
- General chatbots hallucinate features, fail on multispectral data, and ignore radar physics.
- Specialized GIS software is too complex for decision-makers under pressure.

**Core Principle: Simple Outside, Sophisticated Inside.**  
The user enters a question in plain English. Underneath, a controlled, typed agentic graph orchestrates validation, sensor routing, bi-temporal differencing, visual grounding, SAR speckle filtering, and empirical confidence assessment.

---

## 2. High-Level Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                          BHUVISION Web Client                          │
│     (Mission Home  •  Mission View Spatial  •  Workspace  •  Audit)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Gateway Core                           │
│        (Auth & Security  •  CORS  •  Static Storage  •  Routers)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Investigation Orchestrator (LangGraph)               │
│                                                                        │
│   [A1: Planner] ──► [A2: Geo Validator] ──► [A3: Sensor Router]        │
│                             │                         │                │
│                             ▼                         ▼                │
│                     [CRS / Bounds / Geo]     [Optical / SAR Branch]    │
│                                                       │                │
│                             ┌─────────────────────────┴─────────────┐  │
│                             ▼                                       ▼  │
│                   [A4: RS-VQA Specialist]               [A5: Change]│  │
│                             │                         (CV / Diff)   │  │
│                             │                                       ▼  │
│                             └──────────► [A6: Visual Grounding] ◄───┘  │
│                                                  │                     │
│                                                  ▼                     │
│                                        [A7: Evidence Fusion]           │
│                                                  │                     │
│                                                  ▼                     │
│                                    [A8: Confidence & Uncertainty]      │
│                                                  │                     │
│                                                  ▼                     │
│                                        [A9: Audit & Trace]             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
            ┌───────────────────────┴──────────────────────┐
            ▼                                              ▼
┌───────────────────────┐                      ┌───────────────────────┐
│     VLM Inference     │                      │   SAR Radar Engine    │
│ • FreeLLMAPI Gateway  │                      │ • Lee Speckle Filter  │
│ • OmniRoute Gateway   │                      │ • Backscatter (dB)    │
│ • vLLM Server (Local) │                      │ • Specular Water Mask │
│ • Deterministic Demo  │                      │ • Double-Bounce Urban │
└───────────────────────┘                      └───────────────────────┘
```

---

## 3. The 9 Controlled Agents

Each agent inherits from `AgentBase` (`backend/app/agents/base.py`) with guaranteed typed outputs and trace recording:

### Agent 1: Query Planner (`QueryPlannerAgent`)
- **Role:** Understands user inquiry intent without arbitrary LLM code execution.
- **Behavior:** Deterministic keyword and semantic regex parser categorizing requests into:
  - `VQA` (Single-image questions)
  - `CHANGE_DETECTION` (Bi-temporal comparative analysis)
  - `VISUAL_GROUNDING` (Region localization)
  - `SAR_ANALYSIS` (Radar-specific backscatter questions)
- **Output:** `QueryPlan` schema with required tools, sensor needs, and temporal flags.

### Agent 2: Input & Geo Validation (`InputValidationAgent`)
- **Role:** Guards the pipeline from corrupted imagery and CRS projection mismatches.
- **Behavior:** Inspects raster dimensions ($32 \le \text{px} \le 10,000$), file existence, accepted projections (`EPSG:4326`, `EPSG:32632-32635`), and temporal pair chronological ordering.
- **Output:** `ValidationResult` with explicit fatal errors and non-fatal warnings.

### Agent 3: Sensor Router (`SensorRouterAgent`)
- **Role:** Scientifically determines whether to use Optical, SAR, or Optical+SAR.
- **Decision Logic:**
  - Water / Inundation / Flood $\rightarrow$ **SAR Primary** (microwaves penetrate rain and clouds).
  - Urban / Vegetation / Color $\rightarrow$ **Optical Primary** (multispectral resolution).
  - Temporal change $\rightarrow$ **Optical + SAR Fusion** for complementary corroboration.
- **Output:** `SensorDecision` with human-readable rationale.

### Agent 4: Remote-Sensing VQA (`VQAAgent`)
- **Role:** Generates domain-aware natural-language answers about scene characteristics.
- **Behavior:** Injects satellite metadata (sensor, GSD, platform, acquisition season) into the prompt and queries the active `VLMBackend`.
- **Output:** `VQAResult` with raw output, model name, and logits confidence.

### Agent 5: Bi-Temporal Change Detection (`ChangeDetectionAgent`)
- **Role:** Real computer-vision change detection — NOT a placeholder.
- **Pipeline:**
  1. Dimension resampling alignment ($W \times H$).
  2. Luminance grayscale conversion: $Y = 0.299R + 0.587G + 0.114B$.
  3. Absolute pixel differencing: $\Delta I = |I_{t2} - I_{t1}|$.
  4. Adaptive thresholding ($\theta \ge 30$).
  5. Morphological closing and opening with $5 \times 5$ kernel to eliminate speckle noise.
  6. Connected component labeling (`scipy.ndimage.label`) extracting bounding boxes.
- **Output:** `ChangeResult` with change percentage, area in pixels, and bounding coordinates.

### Agent 6: Visual Grounding (`VisualGroundingAgent`)
- **Role:** Highlights supported geographic bounds so users see *where* the answer originated.
- **Behavior:** Converts change detection connected components or saliency variance clusters into pixel and geographic coordinates.
- **Output:** `GroundingResult` and `VisualOverlay` bounding polygons.

### Agent 7: Evidence Fusion (`EvidenceFusionAgent`)
- **Role:** Combines evidence from Optical, SAR, VQA, and change detection into a unified report.
- **Behavior:** Checks for semantic contradictions (e.g., VQA reports "no change" while pixel differencing detects $> 10\%$ change) and flags them explicitly.
- **Output:** `FusedEvidence` with corroborating source items.

### Agent 8: Confidence & Uncertainty (`ConfidenceAgent`)
- **Role:** Honest reliability estimation without fabricated metrics.
- **Rules:**
  - High confidence requires $\ge 3$ corroborating sources and zero contradictions.
  - Moderate confidence for 2 sources.
  - If evidence is ambiguous or uncorroborated, outputs `UNKNOWN` or `LOW` — NEVER fabricates a high number.
- **Output:** `ConfidenceReport` with explicit contributing factors and known uncertainties.

### Agent 9: Audit & Trace (`AuditTraceAgent`)
- **Role:** Generates an observable, legally defensible audit log for government compliance.
- **Output:** `ExecutionTrace` with millisecond timestamps, invoked agent sequence, tools called, model versions, and fallback notices.

---

## 4. SAR Physics & Radar Intelligence

Synthetic Aperture Radar (SAR) operates in the microwave spectrum (Sentinel-1 C-band, $\lambda \approx 5.6\text{ cm}$). Unlike optical sensors, radar signals pass through clouds, smoke, and nighttime conditions.

### Lee Speckle Filter
Multiplicative noise is filtered via local statistics:
$$\hat{R} = \bar{I} + W \cdot (I - \bar{I}), \quad W = \frac{\sigma_I^2 - \bar{I}^2 \sigma_v^2}{\sigma_I^2}$$
where $\bar{I}$ is local mean, $\sigma_I^2$ is local variance, and $\sigma_v^2$ is estimated noise variance.

### Specular Reflection Water Delineation
- Calm water acts as a specular reflector, bouncing radar energy away from the sensor.
- Water threshold: $\sigma^0_{\text{VV}} < -15\text{ dB}$, $\sigma^0_{\text{VH}} < -23\text{ dB}$.
- High backscatter ($> -6\text{ dB}$) corresponds to dihedral double-bounce reflections from vertical urban structures.

---

## 5. Model Serving Layer (`VLMBackend`)

All VLM requests pass through the abstract `VLMBackend` interface:
1. **`GatewayBackend`:** Connects to FreeLLMAPI (`http://localhost:3001/v1`) or OmniRoute (`http://localhost:20128/v1`).
2. **`DemoBackend`:** Fast, verified offline mode for conference judging, ensuring zero-latency, deterministic execution without external network dependency.
3. **`VLLMBackend`:** Local vLLM engine for production deployment with PagedAttention and FP8 quantization.
