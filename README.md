# 🏈 Fantasy NFL Platform  
**Private Codebase · Public Technical Overview**

## Overview

This project is a full-stack Fantasy NFL platform designed to support multi-league play, custom scoring logic, weekly stat ingestion, and both web and mobile clients.

The **production codebase is private** due to ongoing development and potential monetization.  
This public repository serves as a **technical showcase**, documenting system architecture, data flows, API design, and representative implementation patterns.

---

## Key Capabilities

- Custom fantasy scoring engine (weekly + season-level logic)
- Async FastAPI backend
- React web frontend + React Native mobile app
- API-triggered and scheduled scoring jobs
- PostgreSQL persistence
- Deployed production infrastructure (Fly.io backend, Render frontend)

---

## High-Level Architecture

**Frontend**
- React (web)
- React Native / Expo (mobile)

**Backend**
- FastAPI (async-first)
- SQLAlchemy (async sessions)
- REST-based API contracts

**Data Layer**
- PostgreSQL (production)
- JSON-based ingestion for bootstrapping and testing

**Infrastructure**
- Backend deployed on Fly.io
- Frontend deployed on Render
- API-triggered scoring jobs (designed for scheduled automation)

---

## Data Ingestion & Player Loading

### Player Data Flow

1. Player and team data is fetched via a third-party NFL data provider (RapidAPI).
2. Raw data is persisted as a JSON snapshot (e.g. `players_2024.json`) for:
   - Cost control
   - Rate-limit protection
   - Repeatable local and test runs
3. On application startup:
   - The backend checks if the player database is populated
   - If empty, data is loaded from the JSON snapshot into the database

This hybrid approach enables:
- No-cost local development
- Protection against API rate limits
- Deterministic testing without live API calls

---

## Example Backend Responsibilities

Representative backend concerns include:

- Position-based player queries (QB / RB / WR)
- League-scoped scoring execution
- Weekly stat ingestion
- Standings calculation
- Admin-triggered scoring endpoints

Example endpoint pattern:

GET /players/{position}

Returns all players for a given position, sourced from persisted player data.

## Scoring Workflow (High-Level)

1. Player stats are ingested for a given week
2. Scoring logic is executed per league
3. Weekly results are persisted
4. Standings are recalculated
5. Frontend reflects updated rankings

Scoring logic is designed to be:

- Idempotent
- League-isolated
- Triggerable via API (for automation and admin control)

---

## Frontend Overview

The web frontend provides:

- Position-based player browsing
- League standings
- Weekly scoring visibility
- Mobile-responsive UI

The mobile application (React Native) consumes the same API surface as the web frontend, demonstrating shared backend contracts across platforms.

---

## Why the Codebase Is Private

This project represents an actively developed product with potential commercial applications.

To protect intellectual property while still demonstrating technical capability, this repository focuses on:

- System design
- Architectural decisions
- Data flow
- API contracts
- Representative patterns and excerpts

This mirrors how proprietary systems are commonly documented and discussed in professional and startup environments.

---

## What This Project Demonstrates

- End-to-end full-stack system design
- Async backend architecture at production scale
- API-first development
- Real-world data ingestion constraints (cost, rate limits, reliability)
- Deployment and operational considerations
- Clear separation of concerns across layers

---

## Screenshots & Diagrams

Screenshots, architecture diagrams, and sample payloads are included in this repository to illustrate application behavior and system design.

---

## Tech Stack Summary

- Backend: FastAPI (async), SQLAlchemy
- Frontend: React, React Native, Vite
- Database: PostgreSQL
- Infrastructure: Fly.io, Render
- Languages: Python, JavaScript / TypeScript

---

## Notes for Reviewers

If you’d like to see deeper technical details (code samples, schema discussions, scoring logic design), I’m happy to walk through them in a live discussion or technical interview.

---
