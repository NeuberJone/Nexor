# Nexor Architecture

## Overview

Nexor is a modular Manufacturing Execution System (MES) focused on textile print production.

The platform is designed to transform operational production data into structured information for traceability, planning, reporting, and performance analysis. Although machine logs are the initial data source, the architecture is intended to support a broader operational layer that connects production events, roll organization, temporary operator outputs, and future consumption analytics.

---

## Architectural Perspective

Nexor is organized around a production data flow:

```text
Data Ingestion
   ↓
Normalization
   ↓
Production Model
   ↓
Planning
   ↓
Reports
   ↓
Analytics
```

This structure reflects the intended system behavior:

* collect raw operational inputs
* normalize and validate production records
* structure jobs into a consistent production model
* support operational planning decisions
* generate standardized outputs for the floor
* produce metrics and analytical reports

---

## Core Modules

### core

Central domain and infrastructure layer.

Responsibilities:

* shared models
* exceptions
* system configuration
* common utilities
* domain rules used by multiple modules

### logs

Responsible for ingesting and normalizing machine production logs.

Responsibilities:

* parse raw `.txt` logs
* extract job metadata
* calculate production duration
* identify machine source
* normalize production fields
* classify special operational cases such as replacements

### planner

Responsible for production planning before execution.

Responsibilities:

* group jobs by fabric
* estimate length and queue order
* manage roll usage
* allocate jobs with spacing rules
* optionally use available fabric stock

### analytics

Responsible for transforming production data into operational insights.

Responsibilities:

* productivity metrics
* time-per-meter analysis
* bottleneck detection
* reporting of consumption and efficiency

### agent

Local collection layer intended for future hybrid operation.

Responsibilities:

* monitor configured folders
* detect new machine files
* import records automatically
* normalize local data
* synchronize when applicable

---

## Data Sources

Nexor is designed to work with multiple operational data sources.

### 1. Machine production logs

Primary source in the current architecture.

Typical fields may include:

* `ComputerName`
* `JobID`
* `Document`
* `StartTime`
* `EndTime`
* `Driver`
* production size information
* movement and gap-related values

These files are the basis for production traceability.

### 2. Operator-defined planning inputs

Used by the planner module to organize jobs before printing.

Examples:

* image lists
* fabric groupings
* roll assignments
* stock availability

### 3. Printer-generated consumption exports

Future analytical input expected from printer exports.

Possible formats:

* XML
* CSV

These files may later support consumption and cost analysis, depending on the granularity actually provided by the machine.

---

## Machine Identification

Machines are identified through machine-specific fields found in production logs, especially `ComputerName`.

This mapping allows Nexor to associate each record with an internal machine identity such as:

* M1
* M2

Machine identification is required for:

* production history
* machine productivity metrics
* report routing
* export of machine-specific operational summaries

---

## Production Model

The core operational entity of Nexor is the production job.

A production job represents a normalized record of a print event and may include fields such as:

* job identifier
* original document name
* machine
* start time
* end time
* duration
* fabric
* printed length
* gap or spacing information
* classification flags

The architecture separates raw data from normalized data so that machine exports can be preserved while the system still works with standardized internal values.

---

## Replacement Jobs

Replacement files follow a production-specific naming convention that differs from standard jobs.

Examples:

* `N1 - Dryfit`
* `N1 - Dryfit (1)`
* `N1 - Dryfit (2)`

These names should not be treated as independent fabric names merely because the file contains suffixes such as `(1)` or `(2)`.

Instead, the architecture allows the parser to split replacement information into structured components.

Possible parsed fields:

* `job_name`
* `fabric`
* `job_type`
* `operator_code`
* `replacement_index`

Example:

* `job_name = N1 - Dryfit (2)`
* `fabric = Dryfit`
* `job_type = replacement`
* `operator_code = N`
* `replacement_index = 1`

This approach supports two important needs at the same time:

1. avoid fragmentation of the same fabric into false variants caused only by suffix numbering
2. preserve the original operational naming pattern used by the production team

The architecture must also remain flexible enough to allow operator review before final export, because typing inconsistencies and real fabric variations may occur in practice.

Examples of legitimate distinct fabrics:

* `Cacharrel`
* `Cacharrel Verde`

For this reason, Nexor should support operator-side correction of fabric and other fields before final report generation.

---

## Operators Registry

Replacement parsing gains practical value when operator codes can be associated with real people.

For that reason, the system is expected to include a simple operator registry.

Conceptually, this registry allows mapping:

* `N` → `Neuber`

This enables the system to show a full operator name in reports and production views rather than only the original letter code.

---

## Gap Handling and Spacing

Production logs may contain values that represent media advance before print or spacing between print areas.

These values are operationally relevant because they may represent:

* technical gaps
* fabric changes
* roll transitions
* preparation margins
* production waste

The architecture should preserve these values in the normalized model so they can be used by both reporting and planning layers.

---

## Planning Layer

The planner is designed as an operational decision layer rather than only a passive report generator.

Its responsibilities include:

* grouping jobs by fabric
* organizing queue order
* managing roll capacity
* inserting planned spacing between groups
* estimating total print time
* preparing floor-ready export outputs

This layer connects directly with production reality by helping the operator assemble execution-ready roll plans.

---

## Fabric Stock Optimization

The planning layer may optionally use an available stock of fabric to improve material usage.

This stock model is intentionally simple in the initial architecture.

### Supported stock item types

* full rolls
* fabric pieces

### Initial stock model

A simple stock record may include:

* fabric
* length
* type
* created date
* status

This simpler model is preferable to a more complex traceability model when the actual origin of remaining fabric pieces is not consistently documented in the operation.

### Expected behavior

When stock optimization is enabled, Nexor may:

* validate whether a stock item matches the required fabric
* allocate jobs to available pieces before consuming a new roll
* update or remove stock items after planning confirmation

The confirmation step is important because stock changes should happen only after the operator accepts the generated plan.

---

## Report Exports

Nexor follows a multi-output export strategy aligned with real production usage.

Each finalized roll export may generate three different output files with distinct purposes.

### 1. PDF roll report

Purpose:

* permanent report for consultation and history

Destination:

* configurable reports folder

### 2. Mirrored JPG roll archive

Purpose:

* visual record of the exported roll
* backup in case the temporary operator summary is overwritten

Destination:

* roll archive folder

### 3. Mirrored JPG operator summary

Files:

* `Resumo M1.jpg`
* `Resumo M2.jpg`

Purpose:

* machine-facing summary file for immediate operator use
* always reflects the latest exported roll for the target machine

Destination:

* configurable print folder

Behavior:

* overwritten on each new export directed to the respective machine

This architecture deliberately separates permanent exports from temporary operational files so that historical records and printer-facing summaries do not compete for the same location or purpose.

---

## Reporting and Analytics

Beyond operational exports, Nexor is designed to support analytical reporting.

Expected analytical outputs include:

* production by machine
* average time per meter
* performance trends
* bottleneck indicators
* material and ink consumption reports

At this stage, consumption import remains format-dependent and must be validated against actual printer exports. The architecture therefore reserves space for XML and CSV ingestion without assuming a final schema before real samples are analyzed.

---

## Future Hybrid Architecture

The long-term architecture envisions a hybrid structure composed of a local collection layer and a broader platform layer.

Conceptually:

```text
Machines
   ↓
Nexor Agent (local)
   ↓
Nexor Platform
```

In this model, the local agent is responsible for:

* monitoring production folders
* importing new files automatically
* normalizing data close to the source
* continuing operation in unstable connectivity scenarios
* synchronizing with the broader platform when possible

This evolution allows Nexor to scale from a local operational tool into a wider production intelligence platform.

---

## Design Principles

The architecture is guided by the following principles:

* modularity
* traceability
* operational realism
* incremental evolution
* separation between raw inputs and normalized records
* support for both immediate floor use and long-term analytical growth
