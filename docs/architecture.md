# Nexor — Architecture

## 1. Purpose

Nexor is a local-first operational platform for textile production. Its architecture must support real production workflows with a strong focus on traceability, roll closure, historical consultation, planning, structured master data, inventory, and future hybrid expansion.

The system is not designed as a generic utility hub. It must behave as a domain-driven operational product, where logs, jobs, rolls, machines, operators, fabrics, planning, and stock belong to a coherent production model.

---

## 2. Architectural principles

### 2.1 Local-first by default

The core operation must work without internet connectivity.

### 2.2 Domain before interface

The UI should reflect domain structure and workflow, not define them.

### 2.3 Operational simplicity

The architecture must support fast daily actions with low friction.

### 2.4 Progressive modularity

Modules must be separable at the code level, but still integrated at the domain level.

### 2.5 Auditability

Important operational actions must be traceable and reviewable.

### 2.6 Hybrid-ready evolution

Online capabilities should be added as controlled layers, never as a hard dependency for the core workflow.

---

## 3. High-level architecture

Nexor should be structured in layers with clear responsibilities.

### 3.1 Presentation layer

Responsible for user interaction.

Includes:

* operational dashboard
* log inbox / roll assembly view
* roll closure view
* historical search view
* planning view
* inventory view
* master data and settings views

Responsibilities:

* render data
* collect user input
* guide workflow
* display statuses, warnings, and summaries
* prevent destructive mistakes through confirmation and validation

### 3.2 Application layer

Responsible for orchestration of use cases.

Includes services such as:

* import logs
* classify log status
* assemble roll draft
* close roll
* export reports
* search registered rolls
* manage master data
* generate planning estimates
* update inventory balances

Responsibilities:

* coordinate domain operations
* apply workflow rules
* expose use cases to the UI
* keep business scenarios explicit and testable

### 3.3 Domain layer

Responsible for business meaning and rules.

Includes entities such as:

* Log
* Job
* Roll
* Machine
* Operator
* Fabric
* InventoryItem
* ProductionPlan

Responsibilities:

* hold business invariants
* define relationships
* validate core rules
* express lifecycle logic

### 3.4 Infrastructure layer

Responsible for persistence, file access, exports, and external integration.

Includes:

* database repositories
* filesystem readers
* PDF export
* JPG mirror export
* local settings persistence
* future sync adapters
* future backup adapters

Responsibilities:

* interact with files and database
* isolate external dependencies
* keep domain and use cases independent from concrete implementations

---

## 4. Core domains

The project should be organized around functional domains rather than loose screens.

### 4.1 Operations domain

Central domain of the product.

Purpose:
Transform raw production events into structured operational records.

Core responsibilities:

* read logs from configured source
* normalize logs into jobs
* group jobs into roll drafts
* allow operational review
* close and persist rolls
* generate operational exports

### 4.2 Master data domain

Support domain for stable references.

Includes:

* operators
* machines
* fabrics
* aliases and naming normalization rules
* operational defaults and classifications

### 4.3 Search and audit domain

Responsible for historical review.

Includes:

* search filters
* roll detail reconstruction
* traceability navigation
* export regeneration
* inconsistency review

### 4.4 Planning domain

Responsible for pre-production organization.

Includes:

* grouping by fabric
* queue building
* roll capacity allocation
* gap management
* estimated print time
* future layout/fit logic

### 4.5 Inventory domain

Responsible for material tracking.

Includes:

* fabric rolls
* leftover pieces
* stock balance
* reservation or consumption linkage
* future planning integration

### 4.6 Analytics domain

Responsible for performance interpretation.

Includes:

* production metrics
* machine utilization
* time per meter
* operational patterns
* anomaly indicators

### 4.7 Hybrid services domain

Future expansion layer.

Includes:

* optional sync
* backup
* cross-station consolidation
* remote diagnostics
* update channel support

---

## 5. Main entities

### 5.1 Log

Represents the raw operational input from printer-generated files.

Possible fields:

* id
* source_path
* source_name
* captured_at
* machine_code
* raw_payload
* parsed_successfully
* normalized_status
* fingerprint or hash

Purpose:

* preserve raw input identity
* support deduplication
* provide audit trail back to source

### 5.2 Job

Represents a normalized production event derived from a log.

Possible fields:

* id
* log_id
* machine_id
* fabric_id
* operator_id
* job_name
* planned_length_m
* consumed_length_m
* gap_before_m
* actual_printed_length_m
* created_at
* classification
* review_status

Purpose:

* become the operational unit for measurement and traceability
* serve as input for roll consolidation

### 5.3 Roll

Represents an operationally closed production unit composed of jobs.

Possible fields:

* id
* roll_code
* machine_id
* fabric_id
* operator_id
* opened_at
* closed_at
* status
* total_jobs
* total_consumed_length_m
* total_gap_m
* total_actual_printed_length_m
* notes

Purpose:

* represent a real production closure
* consolidate jobs in a traceable structure
* act as a core record for exports, audits, and reporting

### 5.4 Machine

Represents a production machine or equipment reference.

Possible fields:

* id
* code
* name
* category
* active
* notes

### 5.5 Operator

Represents the person associated with the operation.

Possible fields:

* id
* code
* full_name
* active
* notes

### 5.6 Fabric

Represents the production material reference.

Possible fields:

* id
* name
* normalized_name
* aliases
* active
* notes

### 5.7 InventoryItem

Represents a material unit in stock.

Possible fields:

* id
* fabric_id
* item_type
* source_reference
* available_length_m
* reserved_length_m
* consumed_length_m
* status
* notes

### 5.8 ProductionPlan

Represents a future execution plan.

Possible fields:

* id
* fabric_id
* target_roll_length_m
* planned_gap_m
* estimated_time_minutes
* status
* notes

---

## 6. Central relationships

The architecture should preserve the following conceptual relationships:

* one Log generates zero or one normalized Job record in the main flow
* one Job may belong to zero or one Roll
* one Roll aggregates many Jobs
* one Machine may be linked to many Logs, Jobs, and Rolls
* one Operator may be linked to many Jobs and Rolls
* one Fabric may be linked to many Jobs, Rolls, InventoryItems, and ProductionPlans
* Inventory and Planning should depend on stable operational data, not replace it

Critical rule:
A Job should not belong to multiple Rolls unless an explicit reassociation process is introduced and audited.

---

## 7. Data flow

### 7.1 Operational ingestion flow

1. The system reads log files from a configured source folder.
2. Each file is identified, parsed, and validated.
3. A raw Log record is created or matched by fingerprint.
4. Normalization logic transforms valid logs into Job records.
5. Jobs are marked with operational statuses.
6. Eligible jobs appear in the roll assembly workflow.

### 7.2 Roll assembly flow

1. The operator opens the operational inbox.
2. The system lists pending or relevant jobs/logs.
3. The operator selects the jobs that belong to the current roll.
4. The system computes a roll draft summary.
5. Required metadata is confirmed.
6. The Roll is closed and persisted.
7. Linked Jobs are marked as assigned.
8. Exports are generated.

### 7.3 Historical review flow

1. The user searches registered rolls.
2. Filters narrow the result set.
3. A roll detail is opened.
4. The system reconstructs linked jobs and metadata.
5. Exports can be regenerated if needed.

### 7.4 Planning and inventory flow

1. Planning consumes stable operational and master data.
2. Inventory provides availability context.
3. Planning results can later influence operational preparation.
4. Confirmed production may update inventory balances.

---

## 8. State model suggestions

### 8.1 Log states

Suggested statuses:

* new
* parsed
* invalid
* duplicated
* ignored
* converted

### 8.2 Job states

Suggested statuses:

* pending_review
* ready
* suspicious
* assigned_to_roll
* ignored
* corrected

### 8.3 Roll states

Suggested statuses:

* draft
* closed
* exported
* reviewed
* reopened

These states should be explicit in the data model, not implicit in UI behavior.

---

## 9. Application services

The application layer should expose explicit use-case services.

Suggested services:

* `LogImportService`
* `LogParsingService`
* `JobNormalizationService`
* `JobClassificationService`
* `RollDraftService`
* `RollClosureService`
* `RollExportService`
* `RollSearchService`
* `MasterDataService`
* `PlanningService`
* `InventoryService`
* `AnalyticsService`
* `SettingsService`

These names are illustrative, but the principle matters: workflow actions should be separated into reusable orchestration components.

---

## 10. Persistence strategy

### 10.1 Primary mode

A local embedded database should be the default persistence mechanism.

Rationale:

* offline reliability
* simple installation
* low operational dependency
* suitable for single-station or local-network-first scenarios

### 10.2 Persistence boundaries

Separate repositories should exist for major entities:

* logs
* jobs
* rolls
* machines
* operators
* fabrics
* inventory
* plans
* settings

### 10.3 Audit considerations

Where relevant, the architecture should preserve:

* creation timestamps
* update timestamps
* original source references
* correction reasons
* reassociation or reopening history

---

## 11. File and export infrastructure

The infrastructure layer should isolate filesystem and export concerns.

### Required adapters

* source folder scanner
* file parser bridge
* PDF export adapter
* JPG mirror export adapter
* local path validator
* settings loader and saver

### Design rule

Export generation must depend on structured domain data, not directly on raw UI state.

This prevents inconsistent reports and supports reexport.

---

## 12. UI architecture guidelines

Although the UI is not the architecture itself, the code structure should support a screen model with clear responsibilities.

### Suggested presentation sections

* dashboard
* log inbox
* roll draft and closure
* roll search and detail
* planning
* inventory
* master data
* settings

### UI design constraint

Each screen should have one dominant operational purpose.

This is not just a UX preference. It reduces coupling between workflows and makes the system easier to maintain.

---

## 13. Packaging and installability

The architecture should be compatible with a real installed-product experience.

This implies:

* predictable application directories
* bootstrap for initial settings
* automatic local database initialization
* recoverable configuration flow
* internal error logging
* path diagnostics
* future-friendly update strategy

Important distinction:
Packaging an executable is not the same as delivering an installable product.
The architecture must already anticipate installation and runtime concerns.

---

## 14. Hybrid-ready evolution

The architecture should allow future online extensions without rewriting the core.

### Phase 1

* all critical workflows local
* no internet required
* no remote dependency for roll closure or exports

### Phase 2

* optional sync or backup adapters
* optional consolidated reporting
* optional diagnostic or update channels

### Phase 3

* multi-station coordination
* centralized metrics if desired
* distributed yet resilient operation

### Architectural rule

Hybrid services must consume or replicate stable local data. They must not become the source of truth for day-to-day operation too early.

---

## 15. Implementation priority from an architectural perspective

### Priority 1 — Operational core

* log ingestion
* normalization
* job model
* roll model
* classification and status rules
* roll closure flow
* exports

### Priority 2 — Master data

* machines
* operators
* fabrics
* aliases

### Priority 3 — Search and audit

* historical reconstruction
* search filters
* reexport support
* correction visibility

### Priority 4 — Planning

* queue logic
* estimation logic
* roll capacity logic
* gap rules

### Priority 5 — Inventory

* stock representation
* availability logic
* future planning linkage

### Priority 6 — Hybrid expansion

* sync
* backup
* centralization

---

## 16. Architectural summary

Nexor should evolve as a layered, domain-centered, local-first production platform.

Its architecture must preserve a strong operational core, support real-world traceability, remain intuitive at the workflow level, and allow future growth into planning, inventory, analytics, and hybrid services without collapsing into a monolithic utility hub.

### Final definition

**Nexor architecture = local-first operational core + explicit domain model + modular application services + infrastructure isolation + future hybrid readiness.**
