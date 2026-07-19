# project-spec.md

# Multi-Agent DevOps Incident Analysis Suite

**Version:** 1.0 (Hackathon Edition)
**Document Owner:** Principal Solution Architect
**Status:** Approved for Development

---

# Executive Summary

## Project Vision

Build an AI-powered DevOps Incident Analysis platform that automates production incident investigation using a **multi-agent architecture powered by LangGraph**.

The application enables engineers to upload application logs, identify all incidents, perform AI-driven Root Cause Analysis (RCA), retrieve enterprise SOPs using Retrieval Augmented Generation (RAG), recommend remediations, generate executable runbooks, automatically create Jira tickets for critical incidents, and notify Slack channels.

The platform prioritizes:

* Explainability
* Traceability
* Enterprise UI
* Modular architecture
* Zero hallucinated remediations
* Hackathon-friendly implementation

---

# Business Requirements

## Problem Statement

Production incident investigation is slow because engineers must manually:

* Read logs
* Determine root cause
* Search Confluence
* Search SOPs
* Create Jira
* Notify Slack
* Create runbooks

This platform automates these repetitive activities.

---

## Business Objectives

* Reduce MTTR
* Standardize incident analysis
* Improve DevOps productivity
* Demonstrate Agentic AI
* Showcase enterprise-ready architecture

---

# Functional Requirements

## Authentication

* Clerk Authentication
* Login
* Logout
* Session management
* Display logged-in username

---

## Log Upload

Supported:

* .txt
* .log

Future:

* zip
* gz

---

## Incident Detection

The Log Reader Agent shall

* Parse uploaded logs
* Detect ALL incidents
* Extract metadata
* Categorize incidents
* Assign severity
* Calculate confidence

No Jira creation.

No Slack notification.

---

## Root Cause Analysis

The RCA Agent shall provide

* Primary Cause
* Evidence
* Alternative Causes
* Confidence

Never recommend fixes.

---

## Remediation

Uses RAG.

Knowledge Sources

* Confluence
* Google Drive SOPs
* Historical Incidents

Returns

* Ranked recommendations
* Confidence
* Rationale
* Supporting documentation

If no documentation exists

Return

> No supporting documentation found.

Never hallucinate.

This agent prepares the Jira payload.

---

## Cookbook

Display

* Root Cause
* Recommended Steps
* Executable Commands
* Validation
* Rollback

Allow manual Jira creation for non-critical incidents.

---

## Notifications

Critical only

Automatic

* Jira
* Slack

Non-Critical

Manual Jira button

---

# Non Functional Requirements

* Modular
* Stateless APIs
* Explainable AI
* Source traceability
* Configurable RAG
* Responsive UI
* Simple deployment
* Local storage for hackathon

---

# Technology Stack

## Frontend

* Next.js 15
* React
* Tailwind CSS
* shadcn/ui
* Clerk
* React Query
* Framer Motion

## Backend

* FastAPI
* Python
* LangGraph
* LangChain
* Pydantic

## AI

Configurable

* GPT-4.1
* GPT-5

## Embedding

* BAAI/bge-small-en
* nomic-embed-text

## Vector Database

LanceDB

## Integrations

* Jira
* Slack
* Confluence
* Google Drive

---

# High Level Architecture

```
User

↓

Next.js Dashboard

↓

FastAPI Backend

↓

LangGraph Orchestrator

↓

Log Reader

↓

RCA

↓

Remediation

↓

Cookbook

↓

Decision

Critical?

YES
    ↓
 Jira
    ↓
 Slack

NO
    ↓
 Show Manual Jira Button
```

---

# Folder Structure

```
project/

 frontend/

 backend/

 docs/

 tasks/

 .env

 README.md
```

---

# Detailed Folder Structure

```
frontend

 app

 components

 features

 hooks

 lib

 services

 types

backend

 api

 agents

 graph

 rag

 integrations

 models

 services

 config

docs

 project-spec.md

 architecture.md

tasks

 phase-01.md

 phase-02.md

 ...

 phase-13.md
```

---

# API Contracts

## POST

/upload-log

Returns

* uploadId

---

## GET

/incidents

Returns

All incidents

---

## GET

/incidents/{id}

Returns

* RCA
* Remediation
* Cookbook

---

## POST

/create-jira

Creates Jira

---

## POST

/notify-slack

Posts Slack message

---

# LangGraph State

```
Upload

↓

Incidents

↓

Selected Incident

↓

RCA

↓

Remediation

↓

Cookbook

↓

Notification
```

Shared State

* Uploaded Log
* Incident List
* Selected Incident
* Root Cause
* Recommendations
* Cookbook
* Jira Payload

---

# Agent Responsibilities

## Agent 1

Log Reader

Input

Log file

Output

Incident List

Responsibilities

* Parse
* Categorize
* Severity
* Metadata

No Jira

No Slack

---

## Agent 2

RCA

Output

* Primary Cause
* Evidence
* Alternative Causes

---

## Agent 3

Remediation

Uses

* LanceDB
* Confluence
* SOPs

Returns

* Recommendations
* Confidence
* Sources

Builds Jira payload.

---

## Agent 4

Cookbook

Returns

* Runbook
* Validation
* Rollback

Allows manual Jira.

---

## Agent 5

Notification

Critical only

Slack after Jira.

---

# Sequence Diagram

```
User

↓

Upload Log

↓

Log Reader

↓

Display Incidents

↓

Select Incident

↓

RCA

↓

Remediation

↓

Cookbook

↓

Critical?

├──Yes

│     Jira

│       ↓

│    Slack

│

└──No

Create Jira Button
```

---

# Class Diagram

```
LogIssue

Incident

RCAReport

Recommendation

Cookbook

SourceReference

JiraPayload
```

---

# Database Design

Hackathon

Local Storage

LanceDB

Stores

* Embeddings
* Metadata

No relational database required.

---

# Pydantic Models

Core Models

* LogIssue
* Incident
* RCAReport
* Recommendation
* Cookbook
* SourceReference
* JiraPayload

---

# RAG Design

## Sources

Confluence

Google Drive

Historical incidents

---

## Pipeline

Load

↓

Chunk

↓

Embed

↓

Store

↓

Retrieve

↓

Remediation Agent

---

## Weekly Sync

Weekly scheduler

↓

Check modified pages

↓

Re-chunk modified pages only

↓

Update LanceDB

Entire space is never re-indexed.

---

# UI Specification

## Sidebar

* Dashboard
* Upload Logs
* Knowledge Base
* RAG Configuration
* Integrations
* Audit Logs
* Settings
* Help

Dark theme.

---

## Main Workspace

Workflow

1 Log Reader

2 RCA

3 Remediation

4 Cookbook

5 Notification

---

## Left Panel

Display ALL incidents

Each card

* Title
* Service
* Timestamp
* Severity

---

## Main Tabs

* Overview
* RCA
* Recommended Steps
* Cookbook
* Logs
* Metadata

---

## Recommended Steps

Each recommendation shows

* Recommendation
* Confidence
* Reason
* Supporting Sources

Each source shows

* Document Icon
* Document Title
* Confluence/Google Drive badge
* Section
* Last Updated
* Open Link

---

## Cookbook

Displays

* Root Cause
* Recommended Steps
* Commands
* Validation
* Rollback

---

## Bottom Action Panel

Critical

* Automatic Jira
* Automatic Slack

Non-Critical

Button

Create Jira Ticket

---

# Component Hierarchy

```
Dashboard

 Sidebar

 Header

 WorkflowStepper

 IncidentList

 IncidentDetails

 Tabs

 RCA

 Recommendations

 Cookbook

 FooterActions
```

---

# State Management

React Query

Server State

Local React State

UI state

---

# Error Handling

User-friendly messages

Retry options

Empty states

Missing documentation warnings

No AI hallucination fallback

---

# Security

Secrets in .env

No hardcoded keys

Authenticated APIs

HTTPS ready

---

# Environment Variables

```
OPENAI_API_KEY

CLERK_SECRET_KEY

CLERK_PUBLISHABLE_KEY

CONFLUENCE_URL

CONFLUENCE_USER

CONFLUENCE_API_TOKEN

GOOGLE_DRIVE_CREDENTIALS

JIRA_URL

JIRA_EMAIL

JIRA_TOKEN

SLACK_BOT_TOKEN

SLACK_CHANNEL_ID
```

---

# Logging

Application logs

Agent execution logs

API logs

Audit logs

---

# Monitoring

Hackathon

Basic monitoring only

* API health
* Agent execution status
* Error logs

---

# Coding Standards

* SOLID principles
* Modular services
* Type-safe APIs
* Small reusable components
* Clear naming conventions

---

# Git Strategy

```
main

develop

feature/frontend

feature/backend

feature/rag

feature/jira

feature/slack
```

Commit style

```
feat:

fix:

docs:

refactor:

test:
```

---

# Testing Strategy

Frontend

* Component testing

Backend

* API testing

AI

* Prompt validation

Integration

* Jira
* Slack
* Confluence

---

# Deployment Strategy

Hackathon Deployment

Frontend

Vercel

Backend

Render or Railway

Vector DB

Local LanceDB

---

# Risk Register

| Risk            | Mitigation                               |
| --------------- | ---------------------------------------- |
| Missing SOP     | Show "No supporting documentation found" |
| API rate limits | Retry with exponential backoff           |
| Large logs      | File size limit for hackathon            |
| Hallucinations  | Ground responses with RAG only           |

---

# Assumptions

* Confluence access is available
* Google Drive credentials are configured
* Jira project exists
* Slack workspace is configured
* OpenAI API key is valid

---

# Out of Scope

* Real-time log streaming
* Multi-tenancy
* Kubernetes deployment
* RBAC beyond Clerk
* Auto-remediation execution
* Historical analytics dashboard

---

# Architecture Decisions

* LangGraph for orchestration
* LanceDB for lightweight vector storage
* FastAPI for backend APIs
* Next.js for frontend
* Clerk for authentication
* Local storage to simplify hackathon deployment
* Incremental weekly Confluence indexing

---

# Phase-wise Development Plan

## Phase 1 – Project Bootstrap

**Objective:** Establish repository and base architecture.

**Deliverables**

* Frontend scaffold
* Backend scaffold
* Shared project structure

**Tasks**

* Initialize Next.js
* Initialize FastAPI
* Configure Tailwind & shadcn/ui
* Environment configuration

**Acceptance Criteria**

* Application runs locally

**Definition of Done**

* Frontend and backend start successfully

**Suggested Commit**

* `feat: bootstrap project structure`

---

## Phase 2 – Authentication

**Objective:** Secure user access with Clerk.

**Deliverables**

* Login
* Logout
* Username display

**Suggested Commit**

* `feat: integrate Clerk authentication`

---

## Phase 3 – Dashboard UI

**Objective:** Build enterprise dashboard shell.

**Deliverables**

* Sidebar
* Workflow stepper
* Incident list
* Tab layout

**Suggested Commit**

* `feat: build dashboard layout`

---

## Phase 4 – Log Upload

**Objective:** Upload and validate log files.

**Deliverables**

* Upload component
* File validation

**Suggested Commit**

* `feat: implement log upload`

---

## Phase 5 – Log Reader Agent

**Objective:** Parse logs and detect incidents.

**Deliverables**

* Incident classification
* Severity detection
* Incident list

**Suggested Commit**

* `feat: add log reader agent`

---

## Phase 6 – RAG Pipeline

**Objective:** Build knowledge retrieval.

**Deliverables**

* Confluence ingestion
* Google Drive ingestion
* LanceDB indexing
* Weekly incremental sync

**Suggested Commit**

* `feat: implement RAG pipeline`

---

## Phase 7 – RCA Agent

**Objective:** Generate explainable root cause analysis.

**Deliverables**

* Root cause
* Evidence
* Alternative causes

**Suggested Commit**

* `feat: add RCA agent`

---

## Phase 8 – Remediation Agent

**Objective:** Recommend grounded remediations.

**Deliverables**

* Ranked recommendations
* Source references
* Jira payload generation

**Suggested Commit**

* `feat: implement remediation agent`

---

## Phase 9 – Cookbook Agent

**Objective:** Produce executable runbooks.

**Deliverables**

* Commands
* Validation
* Rollback
* Manual Jira option

**Suggested Commit**

* `feat: add cookbook analyzer`

---

## Phase 10 – Jira Integration

**Objective:** Automate ticket creation.

**Deliverables**

* Critical auto-ticket
* Manual ticket for non-critical

**Suggested Commit**

* `feat: integrate Jira`

---

## Phase 11 – Slack Integration

**Objective:** Notify operations teams.

**Deliverables**

* Critical notifications after Jira creation

**Suggested Commit**

* `feat: integrate Slack notifications`

---

## Phase 12 – Testing

**Objective:** Validate end-to-end workflow.

**Deliverables**

* Functional testing
* Integration testing
* UI validation

**Suggested Commit**

* `test: end-to-end validation`

---

## Phase 13 – Deployment

**Objective:** Deploy hackathon-ready solution.

**Deliverables**

* Frontend deployment
* Backend deployment
* Environment configuration
* Demo documentation

**Suggested Commit**

* `chore: deploy hackathon release`

---

# Task Folder Structure

```
tasks/

phase-01-project-bootstrap.md

phase-02-authentication.md

phase-03-dashboard-ui.md

phase-04-log-upload.md

phase-05-log-reader-agent.md

phase-06-rag-pipeline.md

phase-07-rca-agent.md

phase-08-remediation-agent.md

phase-09-cookbook-agent.md

phase-10-jira-integration.md

phase-11-slack-integration.md

phase-12-testing.md

phase-13-deployment.md
```

Each task file should include:

* Objective
* Scope
* Dependencies
* Implementation Tasks
* Deliverables
* Acceptance Criteria
* Definition of Done
* Suggested Git Commit

---

# Future Enhancements

* Streaming log ingestion (Kafka/Splunk)
* Prometheus & Grafana integration
* Historical incident similarity search
* Auto-remediation with approval workflow
* Multi-tenant support
* Role-based access control
* Advanced analytics and MTTR dashboards
* Feedback loop to continuously improve recommendation quality

---

**End of Document**
