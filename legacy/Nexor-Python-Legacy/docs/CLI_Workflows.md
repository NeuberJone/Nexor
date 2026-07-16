# Nexor — CLI Workflows

## 1. Purpose

This document describes the current operational workflows available through the Nexor CLI.

Its goal is to make the local operational flow explicit and reproducible, covering:

* log import
* available job listing
* roll creation
* roll assembly
* roll closure
* roll export
* roll consultation
* bootstrap helper scripts for local validation

This document reflects the current validated CLI flow of the project.

---

## 2. Current CLI Scope

The Nexor CLI currently supports these operational actions:

* import logs from configured sources
* list available jobs for roll assembly
* create rolls
* add jobs to an open roll
* remove jobs from an open roll
* close rolls
* export closed rolls
* list rolls
* inspect roll details

---

## 3. Database Initialization

The CLI initializes the local database automatically on startup through the application entrypoint.

Default database path:

```text
nexor.db
```

In the current local setup, this is typically located at the project root.

---

## 4. Main Entry Point

All core CLI workflows are available through:

```bash
python app.py
```

---

## 5. Log Import Workflow

### Command

```bash
python app.py
```

### Force full rescan

```bash
python app.py --force-rescan
```

### What it does

* loads enabled log sources
* scans for `.txt` log files
* imports raw logs
* detects duplicates
* parses valid logs
* converts valid logs into normalized jobs
* records audit information
* updates source checkpoints

### Output summary

The command prints:

* total logs found
* imported logs
* duplicates
* errors
* planned length
* actual printed length
* gap
* total consumed length

---

## 6. List Available Jobs for Roll Assembly

### Command

```bash
python app.py --list-jobs
```

### Optional filters

Filter by machine:

```bash
python app.py --list-jobs --machine M1
```

Filter by fabric:

```bash
python app.py --list-jobs --fabric DRYFIT
```

Filter by review status:

```bash
python app.py --list-jobs --review-status PENDING_REVIEW
```

Exclude suspicious jobs:

```bash
python app.py --list-jobs --exclude-suspicious
```

Limit number of results:

```bash
python app.py --list-jobs --limit 10
```

### What counts as an available job

A job is considered available when:

* it is not already assigned to any roll
* it is eligible for roll export
* it is not marked with blocked print statuses such as failed, canceled, test, or ignored
* it matches the optional filters when provided

### Output

The command prints one line per available job with:

* internal row id
* job id
* machine
* fabric
* review status
* print status
* effective length
* gap
* consumed length
* document

---

## 7. Create a Roll

### Command

```bash
python app.py --create-roll --roll-machine M1
```

### With fabric and note

```bash
python app.py --create-roll --roll-machine M1 --roll-fabric DRYFIT --roll-note "Novo rolo"
```

### With manual name

```bash
python app.py --create-roll --roll-machine M1 --roll-fabric DRYFIT --roll-name M1_SPECIAL_001
```

### Required arguments

* `--create-roll`
* `--roll-machine`

### Optional arguments

* `--roll-fabric`
* `--roll-note`
* `--roll-name`

### Behavior

* creates a new open roll
* generates the roll name automatically when not provided
* keeps the roll ready for assembly

---

## 8. Add a Job to an Open Roll

### Command

```bash
python app.py --add-job-to-roll --target-roll-id 3 --job-row-id 10
```

### Required arguments

* `--add-job-to-roll`
* `--target-roll-id`
* `--job-row-id`

### Behavior

* validates that the roll exists
* validates that the roll is open
* validates that the job exists
* validates that the job is available for roll assembly
* prevents duplicate assignment
* validates machine compatibility
* validates fabric compatibility when applicable
* inserts the job into the roll snapshot
* prints the updated roll summary

### Important

`job-row-id` is the **internal database row id**, not the textual `job_id`.

---

## 9. Remove a Job from an Open Roll

### Command

```bash
python app.py --remove-job-from-roll --target-roll-id 3 --job-row-id 10
```

### Required arguments

* `--remove-job-from-roll`
* `--target-roll-id`
* `--job-row-id`

### Behavior

* validates that the roll exists
* validates that the roll is open
* removes the selected job from the roll
* prints the updated roll summary

---

## 10. Close a Roll

### Command

```bash
python app.py --close-roll-id 3
```

### With note

```bash
python app.py --close-roll-id 3 --close-note "Fechado manualmente"
```

### Behavior

* validates that the roll exists
* validates that the roll has at least one item
* changes status to `CLOSED`
* stores closure timestamp
* appends note when provided

### Important restriction

A roll cannot be closed when empty.

---

## 11. Export a Closed Roll

### Command

```bash
python app.py --export-roll-id 3
```

### With explicit output directory

```bash
python app.py --export-roll-id 3 --export-output-dir exports/out
```

### Behavior

* validates that the roll exists
* validates that the roll is exportable
* validates that the roll is not empty
* builds export data from persisted roll items
* generates:

  * PDF
  * JPG
* marks the roll as `EXPORTED`
* stores export timestamp

### Output

The command prints:

* roll name
* jobs count
* planned total
* effective total
* gap total
* consumed total
* generated PDF path
* generated JPG path

---

## 12. List Rolls

### Command

```bash
python app.py --list-rolls
```

### Filter by status

```bash
python app.py --list-rolls --roll-status OPEN
python app.py --list-rolls --roll-status CLOSED
python app.py --list-rolls --roll-status EXPORTED
```

### Behavior

The command prints, for each roll:

* id
* roll name
* machine
* fabric
* status
* created timestamp
* closed timestamp
* exported timestamp
* reviewed timestamp
* reopened timestamp
* jobs count
* planned total
* effective total
* gap total
* consumed total
* note
* item list when available

---

## 13. Show Roll Detail

### Command

```bash
python app.py --show-roll-id 3
```

### Behavior

The command prints a detailed operational view of one roll, including:

* roll header
* timestamps
* note
* jobs count
* totals
* efficiency ratio
* metric counts
* fabric totals
* full item detail

This is the most complete inspection command currently available in the CLI.

---

## 14. Bootstrap Helper Scripts

These scripts are useful for local validation and manual testing.

### 14.1 Bootstrap a closed sample roll

```bash
python scripts/bootstrap_sample_roll.py
```

### Purpose

* creates sample jobs
* creates one roll
* assigns jobs
* closes the roll
* prints resulting roll summary

### 14.2 Bootstrap available jobs

```bash
python scripts/bootstrap_available_jobs.py
```

### Purpose

* creates valid jobs
* does not assign them to a roll
* leaves them available for real CLI assembly testing

### 14.3 List rolls through helper script

```bash
python scripts/list_rolls.py
```

### Purpose

* prints rolls directly through the helper script
* useful for manual inspection
* somewhat redundant now that `app.py --list-rolls` exists

---

## 15. Example End-to-End Local Flow

A minimal real local flow can be executed in this order.

### 1. Create available jobs

```bash
python scripts/bootstrap_available_jobs.py
```

### 2. Inspect available jobs

```bash
python app.py --list-jobs
```

### 3. Create a new roll

```bash
python app.py --create-roll --roll-machine M1 --roll-fabric DRYFIT --roll-note "Novo rolo"
```

### 4. Add jobs to the roll

Example with real internal ids:

```bash
python app.py --add-job-to-roll --target-roll-id 3 --job-row-id 3
python app.py --add-job-to-roll --target-roll-id 3 --job-row-id 4
```

### 5. Inspect roll detail

```bash
python app.py --show-roll-id 3
```

### 6. Close the roll

```bash
python app.py --close-roll-id 3 --close-note "Fechado manualmente"
```

### 7. Export the roll

```bash
python app.py --export-roll-id 3 --export-output-dir exports/out
```

### 8. Confirm final state

```bash
python app.py --list-rolls
```

---

## 16. Current Operational Rules

The current CLI behavior follows these rules:

1. a job cannot belong to more than one roll
2. a closed roll cannot be modified
3. an empty roll cannot be closed
4. a non-existent roll cannot be exported
5. roll export must use persisted roll data
6. only available jobs can be added to a roll
7. machine compatibility is enforced
8. fabric compatibility is enforced when both sides define fabric

---

## 17. Open Product Decisions

The following points remain intentionally open and may change later:

* whether `PENDING_REVIEW` jobs should be allowed into rolls
* whether suspicious jobs should be blocked by default
* whether roll creation and assembly should remain CLI-first or move quickly into UI
* whether helper scripts should remain in the repo after the UI becomes primary

---

## 18. Recommended Next Steps

After this document, the most logical next steps are:

1. keep CLI workflows tested
2. decide review-policy for roll eligibility
3. build a lightweight interface on top of the validated CLI/domain flow
4. avoid duplicating logic between helper scripts and the main app entrypoint
