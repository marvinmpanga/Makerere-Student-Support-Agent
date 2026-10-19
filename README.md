# Makerere Student Support & Onboarding Triage Agent

[![CI](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml)
![Lint: Ruff](https://img.shields.io/badge/lint-ruff-261230)
![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow)
![Tests: Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)

**Course:** BSE4104 Emerging Trends in Software Engineering  
**Academic Year:** 2026/2027 | Semester I  
**Course Convener:** Dr. Kamulegeya Grace B. (PhD)  

---

## Team Members & Roles
- **NAKYANZI FARIDAH** - Project & Requirements Lead
- **KAKOOZA MICHEAL OWEN** - Application Lead / DevOps
- **MPANGA MARVIN JOSEPH** - AI Engineering Lead / DevOps
- **LUBEGA LAWRENCE KIRIBWA** - Quality & Security Lead

---

## Project Structure
- `docs/` - Requirements, architecture specs, weekly reports, and evaluation docs.
- `knowledge/` - Controlled policy register and document metadata.
- `prompts/` - Versioned prompt templates and specifications.
- `src/` - Application logic, tools, deterministic validation, and agent loops.
- `tests/` - Unit, integration, and prompt evaluation tests.
- `evidence/` - Execution traces, ClickUp screenshots, and demo assets.

## Download Makerere Policies

Install the project dependencies and run the strict source downloader:

```bash
python -m pip install -r requirements.txt
python -m src.core.download_mak_policies
```

Policy files are stored under `knowledge/raw/mak-policies/`. The downloader
also writes `knowledge/mak-policies-manifest.csv` and records each downloaded
document in `knowledge/source_register.json` with its official source URL.
