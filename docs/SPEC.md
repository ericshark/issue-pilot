# IssuePilot product specification

## Purpose

IssuePilot is both a small issue-submission product and a teaching project. Its
first runnable MVP should be understandable, testable, and completable in one
focused day. The project favors clear boundaries over production-scale
features.

This document defines product requirements. It does not prescribe internal
implementation details or HTTP syntax.

## User and problem

The MVP has one kind of user: a person recording software issues. They need a
quick way to submit an issue and confirm that it was stored.

No authentication or separate roles are required for the MVP.

## MVP user stories

1. As a user, I can enter a title and description and submit an issue.
2. As a user, I can see all submitted issues, newest first.
3. As a user, I can open one submitted issue and see its full description and
   creation time.
4. As a user, I receive a clear validation message when my submission is
   invalid and a clear error message when an operation fails.
5. As a user, I can refresh the application without losing stored issues.

## Issue data in this milestone

Every stored issue has:

- a server-generated positive integer ID;
- a title from 1 to 120 characters after surrounding whitespace is removed;
- a description from 1 to 5,000 characters after surrounding whitespace is
  removed; and
- a server-generated UTC creation timestamp.

Titles and descriptions are plain text. Empty or whitespace-only values are
invalid.

## MVP experience

The interface may be a single page with a submission form and an issue list.
Selecting an issue may show its details on that page; client-side routing is not
required. After a successful submission, the issue appears in the list and the
form is cleared. While a request is running, repeat submission is prevented.

Visual polish, responsive behavior beyond basic usability, and accessibility
beyond semantic labels and keyboard-operable controls are not separate feature
tracks for this one-day MVP.

## Acceptance criteria

The runnable MVP is complete when:

- valid issues can be created through the UI and survive a server restart;
- issues are listed newest first;
- one issue can be retrieved and displayed by ID;
- invalid title or description values are rejected without storing an issue;
- missing issue IDs produce a not-found response;
- frontend and backend use the shapes in `API_CONTRACT.md`; and
- backend behavior is covered by focused Pytest tests.

## Explicitly out of scope

- editing, deleting, closing, assigning, searching, filtering, or paginating
  issues;
- authentication, authorization, multiple users, or organizations;
- attachments, comments, notifications, and external issue-tracker integration;
- deployment, production hardening, and telemetry;
- product AI classification or any Claude API call; and
- storing classification fields before the AI milestone defines their lifecycle.

## Later AI milestone

A later feature will classify an issue by type, priority, component, summary,
rationale, and suggested next action. `AI_BEHAVIOR.md` defines the intended
behavioral boundary. Its API and persistence model require approval before they
are added to the current product and architecture contracts.
