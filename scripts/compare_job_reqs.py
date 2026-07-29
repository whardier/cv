#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml"]
# ///
"""Compare job requirements against the CV taxonomy ontology.

Extracts skills, technologies, domains, compliance requirements, and patterns
from job requirement documents, then cross-references against entities.yaml
and relationships.yaml to produce a coverage report showing:
  - Matched entities (what the candidate already has)
  - Missing entities (gaps in the taxonomy / skills not demonstrated)
  - Relevance scores per category
  - Relationships that demonstrate experience alignment
  - Overall alignment assessment
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_yaml_file(filepath: Path) -> dict:
    """Load a YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def load_job_reqs() -> dict[str, str]:
    """Load all job requirement markdown files."""
    job_reqs_dir = REPO_ROOT / "reference" / "job-reqs"
    texts = {}
    for md_file in sorted(job_reqs_dir.glob("*.md")):
        texts[md_file.stem] = md_file.read_text()
    return texts


# ---------------------------------------------------------------------------
# Term extraction from job requirements
# ---------------------------------------------------------------------------

# Skills/technologies commonly found in job reqs, categorized
JOB_REQ_TERMS = {
    "languages": {
        "Python", "R", "JavaScript", "TypeScript", "SQL", "Bash", "Shell",
        "Go", "Rust", "Java", "C", "C++", "PL/SQL", "Ruby",
    },
    "frameworks_libraries": {
        "FastAPI", "Django", "React", "Redux", "React Native", "VueJS",
        "NuxtJS", "GraphQL", "Serverless Framework", "Celery",
        "scikit-learn", "pandas", "numpy", "TensorFlow", "PyTorch",
        "DoWhy", "EconML", "CausalML", "WeightIt", "MatchIt",
    },
    "platforms_tools": {
        "AWS", "AWS Lambda", "DynamoDB", "SQS", "EventBridge", "Kinesis",
        "S3", "API Gateway", "Athena", "Timestream", "RedShift", "AppSync",
        "GovCloud", "X-Ray", "CloudWatch",
        "Azure", "GCP", "Google Cloud", "Digital Ocean", "CloudFlare",
        "Kubernetes", "Docker", "Terraform", "SaltStack", "Ansible",
        "GitHub Actions", "CircleCI", "ArgoCD", "Jenkins", "Git",
        "DataDog", "Prometheus", "LogicMonitor", "ThousandEyes",
        "OpenTelemetry", "Apache Kafka", "RabbitMQ",
        "Okta", "Jamf", "Kandji", "Google Workspace",
        "PostgreSQL", "MongoDB", "Redis", "Snowflake", "SnowflakeDB",
        "Oracle", "Intersystems IRIS",
    },
    "protocols_standards": {
        "SAML", "OAuth", "OAuth 2.0", "SCIM", "SSO", "MFA",
        "REST API", "REST APIs", "webhooks",
        "SNMP", "SIP", "IAX", "SMTP", "HL7", "FHIR", "HL7/FHIR", "DICOM",
        "DNS", "HTTP", "VPN",
    },
    "methodologies": {
        "Machine Learning", "AI", "Data Science", "Causal Inference",
        "Deep Learning", "Predictive Analytics", "Statistical Inference",
        "CI/CD", "Infrastructure as Code", "IaC", "DevSecOps",
        "GitOps", "Prompt Engineering", "LLM", "Agentic Workflows",
        "Penetration Testing", "Dependency Scanning",
        "Synthetic Data Generation", "Causal Machine Learning",
    },
    "compliance": {
        "HIPAA", "SOC 2", "SOC II", "SOC I/II", "ISO 27001",
        "FedRAMP", "OWASP", "Zero-Trust", "BeyondCorp",
        "CMS", "Medicare", "Medicaid",
    },
    "patterns": {
        "Clean Architecture", "Domain-Driven Design", "DDD",
        "Event-Driven Architecture", "Microservice", "Microservices",
        "Serverless Architecture", "Asynchronous Process Design",
        "Zero-Trust Architecture", "Platform as a Service",
        "Distributed Tracing", "Edge Computing",
    },
    "domains": {
        "Healthcare", "SaaS", "Security", "Cybersecurity",
        "Telecommunications", "IoT", "Federal", "Government",
        "Finance", "Enterprise", "Identity", "Authentication",
        "Authorization", "Endpoint Management", "MDM",
        "Fleet Management", "IT Automation",
    },
}


def extract_terms_from_text(text: str) -> dict[str, set[str]]:
    """Extract all recognized terms from a job requirement text."""
    found = defaultdict(set)
    for category, terms in JOB_REQ_TERMS.items():
        for term in terms:
            if len(term) <= 2:
                # Very short terms: exact case-sensitive match with word boundaries
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text):
                    found[category].add(term)
            elif len(term) <= 3:
                # Short terms (3 chars): case-sensitive with word boundaries
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text):
                    found[category].add(term)
            else:
                # Longer terms: case-insensitive
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found[category].add(term)
    return dict(found)


# ---------------------------------------------------------------------------
# Entity matching
# ---------------------------------------------------------------------------

# Map common job-req terms to entity IDs in the taxonomy
TERM_TO_ENTITY_MAP = {
    # Languages
    "Python": "skill-python",
    "R": None,  # Not in taxonomy
    "JavaScript": "skill-javascript",
    "TypeScript": "skill-typescript",
    "SQL": None,  # Not a standalone entity
    "Bash": "skill-shell",
    "Shell": "skill-shell",
    "C": "skill-c",
    "C++": "skill-cpp",
    "PL/SQL": "skill-pl-sql",
    "Go": None,
    "Rust": None,
    "Java": None,
    "Ruby": None,
    # Frameworks
    "FastAPI": "skill-fastapi",
    "Django": "skill-django",
    "React": "skill-react",
    "Redux": "skill-redux",
    "React Native": "skill-react-native",
    "VueJS": "skill-vuejs",
    "NuxtJS": "skill-nuxtjs",
    "GraphQL": "skill-graphql",
    "Serverless Framework": "skill-serverless-framework",
    "Celery": "skill-celery",
    "scikit-learn": None,  # Not a standalone entity (covered by Python/ML)
    "pandas": None,
    "numpy": None,
    "TensorFlow": None,
    "PyTorch": None,
    "DoWhy": None,
    "EconML": None,
    "CausalML": None,
    "WeightIt": None,
    "MatchIt": None,
    # Platforms/Tools
    "AWS": "skill-aws",
    "AWS Lambda": "skill-aws-lambda",
    "DynamoDB": "skill-aws-dynamodb",
    "SQS": "skill-aws-sqs",
    "EventBridge": "skill-aws-eventbridge",
    "Kinesis": "skill-aws-kinesis",
    "S3": "skill-aws-s3",
    "API Gateway": "skill-aws-api-gateway",
    "Athena": "skill-aws-athena",
    "Timestream": "skill-aws-timestream",
    "RedShift": "skill-aws-redshift",
    "AppSync": "skill-aws-appsync",
    "GovCloud": "skill-aws-govcloud",
    "X-Ray": "skill-aws-x-ray",
    "CloudWatch": "skill-aws-cloudwatch",
    "Azure": "skill-azure",
    "GCP": None,
    "Google Cloud": None,
    "Digital Ocean": "skill-digital-ocean",
    "CloudFlare": "skill-cloudflare",
    "Kubernetes": "skill-kubernetes",
    "Docker": "skill-docker",
    "Terraform": "skill-terraform",
    "SaltStack": "skill-saltstack",
    "Ansible": "skill-ansible",
    "GitHub Actions": "skill-github-actions",
    "CircleCI": "skill-circleci",
    "ArgoCD": "skill-argocd",
    "Jenkins": "skill-jenkins",
    "Git": "skill-git",
    "DataDog": "skill-datadog",
    "Prometheus": "skill-prometheus",
    "LogicMonitor": "skill-logicmonitor",
    "ThousandEyes": "skill-thousandeyes",
    "OpenTelemetry": "skill-opentelemetry",
    "Apache Kafka": "skill-apache-kafka",
    "RabbitMQ": "skill-rabbitmq",
    "Okta": None,
    "Jamf": None,
    "Kandji": None,
    "Google Workspace": None,
    "PostgreSQL": "skill-postgresql",
    "MongoDB": "skill-mongodb",
    "Redis": "skill-redis",
    "Snowflake": "skill-snowflakedb",
    "SnowflakeDB": "skill-snowflakedb",
    "Oracle": "skill-oracle",
    "Intersystems IRIS": "skill-intersystems-iris-cache",
    # Protocols
    "SAML": None,
    "OAuth": None,
    "OAuth 2.0": None,
    "SCIM": None,
    "SSO": None,
    "MFA": None,
    "REST API": None,
    "REST APIs": None,
    "webhooks": None,
    "SNMP": "skill-snmp",
    "SIP": "skill-sip-iax",
    "IAX": "skill-sip-iax",
    "SMTP": "skill-smtp",
    "HL7": "skill-hl7-fhir",
    "FHIR": "skill-hl7-fhir",
    "HL7/FHIR": "skill-hl7-fhir",
    "DICOM": "skill-dicom",
    "DNS": None,
    "HTTP": None,
    "VPN": None,
    # Methodologies
    "Machine Learning": "skill-machine-learning",
    "AI": None,  # Too broad to map
    "Data Science": None,  # Not a specific entity
    "Causal Inference": None,
    "Deep Learning": None,
    "Predictive Analytics": "pattern-predictive-analytics",
    "Statistical Inference": None,
    "CI/CD": "skill-ci-cd",
    "Infrastructure as Code": "skill-infrastructure-as-code",
    "IaC": "skill-infrastructure-as-code",
    "DevSecOps": "skill-devsecops",
    "GitOps": None,
    "Prompt Engineering": "skill-prompt-engineering",
    "LLM": "skill-prompt-engineering",
    "Agentic Workflows": "pattern-agentic-engineering",
    "Penetration Testing": "skill-penetration-testing",
    "Dependency Scanning": "skill-dependency-scanning",
    "Synthetic Data Generation": "skill-synthetic-data-generation",
    "Causal Machine Learning": None,
    # Compliance
    "HIPAA": "compliance-hipaa",
    "SOC 2": "compliance-soc-i-ii",
    "SOC II": "compliance-soc-i-ii",
    "SOC I/II": "compliance-soc-i-ii",
    "ISO 27001": None,
    "FedRAMP": "compliance-fedramp",
    "OWASP": "compliance-owasp",
    "Zero-Trust": "compliance-zero-trust-beyondcorp",
    "BeyondCorp": "compliance-zero-trust-beyondcorp",
    "CMS": "compliance-cms",
    "Medicare": "compliance-medicare-medicaid",
    "Medicaid": "compliance-medicare-medicaid",
    # Patterns
    "Clean Architecture": "pattern-clean-architecture",
    "Domain-Driven Design": "pattern-domain-driven-design",
    "DDD": "pattern-domain-driven-design",
    "Event-Driven Architecture": "pattern-event-driven-architecture",
    "Microservice": "pattern-microservice-architecture",
    "Microservices": "pattern-microservice-architecture",
    "Serverless Architecture": "pattern-serverless-architecture",
    "Asynchronous Process Design": "pattern-asynchronous-process-design",
    "Zero-Trust Architecture": "pattern-zero-trust-architecture",
    "Platform as a Service": "pattern-platform-as-a-service",
    "Distributed Tracing": "pattern-distributed-tracing",
    "Edge Computing": "domain-edge-computing",
    # Domains
    "Healthcare": "domain-healthcare",
    "SaaS": "domain-saas-product",
    "Security": "domain-security",
    "Cybersecurity": "domain-security",
    "Telecommunications": "domain-telecommunications",
    "IoT": "domain-iot-industrial",
    "Federal": "domain-federal-government",
    "Government": "domain-federal-government",
    "Finance": "domain-finance-enterprise",
    "Enterprise": "domain-finance-enterprise",
    "Identity": None,
    "Authentication": None,
    "Authorization": None,
    "Endpoint Management": None,
    "MDM": None,
    "Fleet Management": None,
    "IT Automation": None,
}


def match_entities(extracted_terms: dict[str, set[str]], entities: dict) -> dict:
    """Match extracted job req terms against taxonomy entities."""
    matched = {}  # entity_id -> {term, category, entity_name}
    missing = {}  # term -> category (terms with no entity match)

    # Build entity id -> name lookup
    id_to_name = {}
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    id_to_name[item["id"]] = item.get("name", item["id"])

    for category, terms in extracted_terms.items():
        for term in terms:
            entity_id = TERM_TO_ENTITY_MAP.get(term)
            if entity_id is not None:
                entity_name = id_to_name.get(entity_id, entity_id)
                matched[entity_id] = {
                    "term": term,
                    "category": category,
                    "entity_name": entity_name,
                }
            else:
                missing[term] = category

    return {"matched": matched, "missing": missing}


# ---------------------------------------------------------------------------
# Relationship matching
# ---------------------------------------------------------------------------

def find_relevant_relationships(
    matched_entity_ids: set[str],
    relationships: list[dict],
    entities: dict,
) -> list[dict]:
    """Find relationships that demonstrate alignment with matched entities.

    Returns relationships where the subject or object (or context references)
    intersect with the entities required by the job.
    """
    id_to_name = {}
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    id_to_name[item["id"]] = item.get("name", item["id"])

    relevant = []
    for rel in relationships:
        subject = rel.get("subject", "")
        obj = rel.get("object", "")
        predicate = rel.get("predicate", "")
        context = rel.get("context", {})

        # Check if subject or object matches a required entity
        matches_subject = subject in matched_entity_ids
        matches_object = obj in matched_entity_ids

        # Also check context fields (domain, compliance, co_skills)
        context_matches = set()
        for key, val in context.items():
            if isinstance(val, str) and val in matched_entity_ids:
                context_matches.add(val)
            elif isinstance(val, list):
                for v in val:
                    if isinstance(v, str) and v in matched_entity_ids:
                        context_matches.add(v)

        if matches_subject or matches_object or context_matches:
            relevance_score = 0
            if matches_subject:
                relevance_score += 2
            if matches_object:
                relevance_score += 2
            relevance_score += len(context_matches)

            relevant.append({
                "subject": subject,
                "subject_name": id_to_name.get(subject, subject),
                "predicate": predicate,
                "object": obj,
                "object_name": id_to_name.get(obj, obj),
                "context": context,
                "relevance_score": relevance_score,
                "matched_entities": (
                    ([subject] if matches_subject else [])
                    + ([obj] if matches_object else [])
                    + list(context_matches)
                ),
            })

    # Sort by relevance score descending
    relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
    return relevant


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_alignment_score(match_result: dict, relevant_rels: list[dict]) -> dict:
    """Compute an overall alignment score for the job requirement."""
    matched = match_result["matched"]
    missing = match_result["missing"]

    total_terms = len(matched) + len(missing)
    if total_terms == 0:
        return {"overall": 0.0, "breakdown": {}}

    # Category-level coverage
    category_counts = defaultdict(lambda: {"matched": 0, "missing": 0})
    for entity_id, info in matched.items():
        category_counts[info["category"]]["matched"] += 1
    for term, category in missing.items():
        category_counts[category]["missing"] += 1

    breakdown = {}
    for cat, counts in category_counts.items():
        total = counts["matched"] + counts["missing"]
        pct = (counts["matched"] / total * 100) if total > 0 else 0
        breakdown[cat] = {
            "matched": counts["matched"],
            "missing": counts["missing"],
            "total": total,
            "coverage_pct": round(pct, 1),
        }

    # Overall coverage percentage
    overall_coverage = (len(matched) / total_terms * 100) if total_terms > 0 else 0

    # Relationship depth bonus: having relevant relationships shows depth
    rel_bonus = min(len(relevant_rels) * 0.5, 15.0)  # Cap at 15% bonus

    # Final score (capped at 100)
    final_score = min(overall_coverage + rel_bonus, 100.0)

    return {
        "overall_coverage_pct": round(overall_coverage, 1),
        "relationship_bonus": round(rel_bonus, 1),
        "final_score": round(final_score, 1),
        "breakdown": breakdown,
        "total_matched": len(matched),
        "total_missing": len(missing),
        "total_terms": total_terms,
        "relevant_relationships": len(relevant_rels),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def print_job_report(
    job_name: str,
    extracted_terms: dict[str, set[str]],
    match_result: dict,
    relevant_rels: list[dict],
    score: dict,
    entities: dict,
):
    """Print a detailed report for one job requirement."""
    print("\n" + "=" * 76)
    print(f"  JOB REQUIREMENT: {job_name}")
    print("=" * 76)

    # --- Extracted Terms ---
    print("\n" + "-" * 76)
    print("  EXTRACTED TERMS")
    print("-" * 76)
    total_extracted = sum(len(v) for v in extracted_terms.values())
    print(f"\n  Total terms extracted: {total_extracted}")
    for category, terms in sorted(extracted_terms.items()):
        print(f"\n  [{category.upper()}] ({len(terms)} terms)")
        for term in sorted(terms):
            print(f"    - {term}")

    # --- Matched Entities ---
    print("\n" + "-" * 76)
    print("  MATCHED ENTITIES (Covered by Taxonomy)")
    print("-" * 76)
    matched = match_result["matched"]
    print(f"\n  Total matched: {len(matched)}")
    by_cat = defaultdict(list)
    for entity_id, info in matched.items():
        by_cat[info["category"]].append((info["term"], info["entity_name"], entity_id))
    for cat in sorted(by_cat):
        print(f"\n  [{cat.upper()}]")
        for term, name, eid in sorted(by_cat[cat]):
            if term != name:
                print(f"    + {term} -> {name} ({eid})")
            else:
                print(f"    + {name} ({eid})")

    # --- Missing Entities (Gaps) ---
    print("\n" + "-" * 76)
    print("  MISSING ENTITIES (Gaps - Not in Taxonomy)")
    print("-" * 76)
    missing = match_result["missing"]
    print(f"\n  Total gaps: {len(missing)}")
    missing_by_cat = defaultdict(list)
    for term, cat in missing.items():
        missing_by_cat[cat].append(term)
    for cat in sorted(missing_by_cat):
        print(f"\n  [{cat.upper()}]")
        for term in sorted(missing_by_cat[cat]):
            print(f"    - {term}")

    # --- Relevant Relationships ---
    print("\n" + "-" * 76)
    print("  RELEVANT RELATIONSHIPS (Demonstrating Experience Alignment)")
    print("-" * 76)
    print(f"\n  Total relevant relationships: {len(relevant_rels)}")
    if relevant_rels:
        # Show top relationships grouped by predicate
        by_predicate = defaultdict(list)
        for rel in relevant_rels:
            by_predicate[rel["predicate"]].append(rel)

        for pred in sorted(by_predicate):
            rels = by_predicate[pred]
            print(f"\n  [{pred}] ({len(rels)} relationships)")
            # Show top 10 per predicate
            for rel in rels[:10]:
                ctx = rel["context"]
                timeframe = ctx.get("timeframe", "")
                org = ctx.get("organization", "")
                domain = ctx.get("domain", "")
                context_parts = []
                if timeframe:
                    context_parts.append(timeframe)
                if org:
                    context_parts.append(f"org={org}")
                if domain:
                    context_parts.append(f"domain={domain}")
                ctx_str = " | ".join(context_parts)
                print(f"    {rel['subject_name']} -> {rel['object_name']}")
                if ctx_str:
                    print(f"      [{ctx_str}]")
            if len(rels) > 10:
                print(f"    ... and {len(rels) - 10} more")

    # --- Alignment Score ---
    print("\n" + "-" * 76)
    print("  ALIGNMENT SCORE")
    print("-" * 76)
    print(f"\n  Overall Coverage:        {score['overall_coverage_pct']}%")
    print(f"  Relationship Bonus:      +{score['relationship_bonus']}%")
    print(f"  Final Alignment Score:   {score['final_score']}%")
    print(f"\n  Matched: {score['total_matched']} / {score['total_terms']} terms")
    print(f"  Relevant Relationships:  {score['relevant_relationships']}")

    print("\n  Category Breakdown:")
    for cat, data in sorted(score["breakdown"].items()):
        bar_len = int(data["coverage_pct"] / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"    {cat:<25s} [{bar}] {data['coverage_pct']:5.1f}% ({data['matched']}/{data['total']})")

    # --- Assessment ---
    print("\n" + "-" * 76)
    print("  ASSESSMENT")
    print("-" * 76)
    final = score["final_score"]
    if final >= 80:
        level = "STRONG ALIGNMENT"
        desc = "The taxonomy demonstrates strong coverage of this role's requirements."
    elif final >= 60:
        level = "GOOD ALIGNMENT"
        desc = "The taxonomy covers most requirements with some notable gaps."
    elif final >= 40:
        level = "MODERATE ALIGNMENT"
        desc = "The taxonomy covers core elements but has significant gaps in specialized areas."
    elif final >= 20:
        level = "PARTIAL ALIGNMENT"
        desc = "Limited overlap between the taxonomy and this role's requirements."
    else:
        level = "LOW ALIGNMENT"
        desc = "Minimal coverage of this role's specialized requirements."

    print(f"\n  {level}")
    print(f"  {desc}")

    if missing:
        print("\n  Key gaps to address:")
        # Highlight the most impactful missing terms
        priority_missing = [t for t, c in missing.items()
                          if c in ("languages", "frameworks_libraries", "platforms_tools", "methodologies")]
        if priority_missing:
            for term in sorted(priority_missing)[:10]:
                print(f"    * {term}")

    print()


def main():
    """Run job requirement comparison analysis."""
    tax_dir = REPO_ROOT / "taxonomy"

    # Load taxonomy
    entities = load_yaml_file(tax_dir / "entities.yaml")
    rel_data = load_yaml_file(tax_dir / "relationships.yaml")
    relationships = rel_data.get("relationships", [])

    # Load job requirements
    job_reqs = load_job_reqs()

    if not job_reqs:
        print("ERROR: No job requirement documents found in reference/job-reqs/")
        return 1

    print("=" * 76)
    print("  CV ONTOLOGY vs JOB REQUIREMENTS - COMPARISON REPORT")
    print("=" * 76)
    print(f"\n  Taxonomy: {sum(len(v) for v in entities.values() if isinstance(v, list))} entities, {len(relationships)} relationships")
    print(f"  Job Requirements: {len(job_reqs)} document(s)")
    for name in sorted(job_reqs):
        print(f"    - {name}")

    all_scores = {}

    for job_name, text in sorted(job_reqs.items()):
        # Step 1: Extract terms from job req
        extracted_terms = extract_terms_from_text(text)

        # Step 2: Match against entities
        match_result = match_entities(extracted_terms, entities)

        # Step 3: Find relevant relationships
        matched_ids = set(match_result["matched"].keys())
        relevant_rels = find_relevant_relationships(matched_ids, relationships, entities)

        # Step 4: Compute alignment score
        score = compute_alignment_score(match_result, relevant_rels)
        all_scores[job_name] = score

        # Step 5: Print report
        print_job_report(job_name, extracted_terms, match_result, relevant_rels, score, entities)

    # --- Comparative Summary ---
    if len(all_scores) > 1:
        print("\n" + "=" * 76)
        print("  COMPARATIVE SUMMARY")
        print("=" * 76)
        print(f"\n  {'Job Requirement':<45s} {'Coverage':>10s} {'Score':>8s}")
        print(f"  {'-' * 45} {'-' * 10} {'-' * 8}")
        for name, score in sorted(all_scores.items(), key=lambda x: x[1]["final_score"], reverse=True):
            print(f"  {name:<45s} {score['overall_coverage_pct']:>8.1f}%  {score['final_score']:>6.1f}%")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
