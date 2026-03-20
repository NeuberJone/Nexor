# Nexor — Functional Specification: Operational Core v0.1

## 1. Purpose

This document defines the functional behavior of the Nexor operational core. It describes the minimum end-to-end flow required for the first implementation cycle: import logs, parse data, normalize jobs, assemble a roll draft, close the roll, export outputs, and allow historical consultation with re-export support.

The purpose of this specification is to make the operational flow explicit before implementation, reducing ambiguity between product vision, domain logic, and interface behavior.

## 2. Scope

### Included in v0.1

* log import
* parsing and validation
* job normalization
* operational roll assembly
* roll closure
* PDF export
* JPG mirror export
* basic historical consultation
* basic re-export
* minimum master data support

### Out of scope for v0.1

* advanced queue planning
* detailed inventory workflow
* advanced analytics
* online synchronization
* automated backup
* distributed multi-station operation

## 3. Primary Actors

### Production Operator

Uses the system to work with operational records and build roll drafts.

### Reviewer / Closure Responsible

Validates the draft, confirms final data, closes the roll, and triggers formal outputs.

### Master Data Administrator

Maintains minimum references such as machines, operators, fabrics, and aliases.

### Nexor System

Imports, validates, normalizes, persists, recalculates, and exports according to defined rules.

## 4. Operational Flow Overview

The operational core follows this sequence:

1. the system imports new source logs
2. valid logs are parsed
3. parsed logs are normalized into jobs
4. eligible jobs appear in the operational workspace
5. the user assembles or reviews a roll draft
6. the user closes the roll
7. the system exports formal outputs
8. the roll becomes available for historical consultation and re-export

## 5. Functional Modules

The v0.1 operational core is organized into the following functional modules:

* Log Import
* Parsing and Validation
* Job Normalization
* Operational Roll Assembly
* Roll Closure
* Export
* Historical Search
* Minimum Master Data

## 6. Functional Rules by Module

### 6.1 Log Import

#### Objective

Read raw source files and register only new valid import candidates.

#### Inputs

* configured source folder
* compatible source files

#### Outputs

* imported logs
* duplicated logs
* invalid logs

#### Rules

* each imported source entry must generate a fingerprint
* duplicates must not be silently reprocessed
* previously imported data must remain intact when a new batch is imported
* raw source origin must always be preserved

### 6.2 Parsing and Validation

#### Objective

Extract the minimum operational fields required from imported raw content.

#### Expected minimum fields

* job name
* timestamp when available
* printed height
* raw machine identification when available

#### Rules

* invalid logs must remain traceable
* parsing failure must not erase source origin
* `HeightMM` must be valid for length calculation
* partial parsing should remain explicit and auditable

### 6.3 Job Normalization

#### Objective

Transform a parsed `Log` into a usable `Job`.

#### Rules

* the raw job name must be preserved
* a normalized job name must be derived without destroying the original text
* fabric aliases should be used to resolve official `Fabric` when possible
* `actual_printed_length_m = height_mm / 1000`
* `vpos_mm` is offset, not printed length
* inconsistent or ambiguous records must become `suspicious`, not be discarded automatically
* correction actions must be traceable

### 6.4 Operational Roll Assembly

#### Objective

Allow the user to assemble and review a roll draft from eligible jobs.

#### Rules

* only eligible jobs should appear for roll assembly
* suspicious jobs may require explicit review before inclusion
* the draft summary must always be recalculated from persisted or current structured selection data
* draft composition may change only while roll status is `draft`

#### Minimum summary shown to the user

* total jobs
* selected or inferred fabric
* selected or inferred machine
* total printed length
* pending alerts or review markers

### 6.5 Roll Closure

#### Objective

Consolidate the roll draft into a closed and auditable operational record.

#### Preconditions

* at least one job is selected
* required roll metadata is filled
* totals are recalculated by the backend/application logic

#### Rules

* closing a roll freezes its composition
* included jobs must be marked as assigned
* closure data must not depend on the visual state of the interface
* reopening must remain exceptional and auditable

### 6.6 Export

#### Objective

Generate formal outputs for a closed roll.

#### Minimum outputs

* PDF
* JPG mirror

#### Rules

* exports must be generated from persisted roll data
* export path and timestamp must be recorded
* re-export must use the historical roll record, not a manually rebuilt draft

### 6.7 Historical Search

#### Objective

Allow users to locate previously closed rolls and inspect their data.

#### Minimum filters

* machine
* fabric
* roll name or code
* period/date range

#### Minimum actions

* open roll detail
* inspect related jobs
* re-export

### 6.8 Minimum Master Data

#### Objective

Support normalization, consistency, and traceability.

#### Included in v0.1

* machines
* operators
* fabrics
* fabric aliases

#### Rules

* master data should remain simple in v0.1
* aliases support normalization but do not replace the official fabric name
* master data changes must affect future processing without corrupting historical closed records

## 7. Functional Requirements Summary

The v0.1 operational core must be able to:

* import logs without silent duplication
* preserve raw origin
* normalize jobs with traceability
* assemble a roll draft from eligible jobs
* close a roll with frozen composition
* export PDF and JPG mirror outputs
* support historical consultation and re-export

## 8. Essential Non-Functional Requirements

The operational core must also satisfy the following non-functional requirements:

* local-first execution
* responsive behavior in local environment
* auditability
* clear separation between domain logic and interface
* tolerance for incomplete or ambiguous data through explicit status marking

## 9. Relevant States in the Flow

### Log

* `new`
* `parsed`
* `invalid`
* `duplicated`
* `ignored`
* `converted`

### Job

* `pending_review`
* `ready`
* `suspicious`
* `assigned_to_roll`
* `ignored`
* `corrected`

### Roll

* `draft`
* `closed`
* `exported`
* `reviewed`
* `reopened`

## 10. Exception and Critical Scenarios

The specification must explicitly consider these scenarios:

* duplicated log detected on import
* partial parsing
* ambiguous job name
* unresolved fabric
* suspicious job awaiting review
* attempt to close an empty roll
* attempt to export a non-existent roll
* reopening after export

## 11. Explicitly Out of Scope in v0.1

The following flows are intentionally deferred:

* detailed queue planning
* inventory with source roll tracking
* advanced analytics dashboards
* remote backend synchronization
* automated backup workflows

## 12. Document Dependencies

This document should be read together with:

* `README.md`
* `Architecture.md`
* `Roadmap.md`
* `UI_UX_Specification.md`
* `Wireframe_Specification.md`
* `Data_Model.md`

## 13. Next Steps After Approval

Once this functional specification is approved, the next steps are:

1. detail use cases for the operational core
2. define service contracts
3. map persistence structure
4. start the operational core code skeleton