# Documentation Index

This folder contains both public-facing guides and milestone-specific runbooks. If you are new to the repository, start with the top-level files first.

## Start here

- [README.md](../README.md) - product overview, quick start, architecture summary, deployment links
- [CONTRIBUTING.md](../CONTRIBUTING.md) - local setup, testing, code style, and pull request expectations
- [ARCHITECTURE.md](../ARCHITECTURE.md) - module map, runtime layers, and design assumptions

## Deployment guides

- [Render deployment guide](render-free-deployment-guide.md)
- [Railway deployment guide](railway-deployment-guide.md)
- [Hugging Face Spaces deployment guide](huggingface-spaces-deployment-guide.md)
- [Hugging Face post-deploy QA checklist](huggingface-post-deploy-qa-checklist.md)

## Testing and verification runbooks

- [How to Test M4](how-to-test-m4.md)
- [How to Test M5](how-to-test-m5.md)
- [How to Test M6](how-to-test-m6.md)
- [How to Test M7](how-to-test-m7.md)
- [How to Test M8](how-to-test-m8.md)
- [How to Test M9](how-to-test-m9.md)

## Historical implementation notes

These files capture milestone-specific implementation context and verification output.
They are useful when you need to understand why a change was made or how a previous
milestone was validated.

- [Implementation log](implementation-log.md)
- [Milestone checklist](milestone-checklist.md)
- [MVP full scope reference](mvp-full.md)
- [How to test M1](how-to-test-m1.md) and related milestone files

## Working on the repository

If you are changing code, use the docs above as the source of truth for:

- supported user journeys
- deployment assumptions
- test commands
- artifact locations
- the approval gate and deterministic fallback policy

The public README and these docs should stay aligned with the actual codebase.
