#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml"]
# ///
"""Extract taxonomy entities and relationships from CV reference documents.

WARNING: This is a ONE-SHOT SEED SCRIPT. Running it will OVERWRITE any manual
edits to the taxonomy/*.yaml files. The YAML artifacts are the source of truth
going forward. Use --dry-run to preview output without writing files.

Parses reference/original-cv.md, reference/officehours-profile.md, and
reference/officehours-profile.json to build structured YAML taxonomy artifacts.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from collections import OrderedDict

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

def slugify(text: str, prefix: str = "") -> str:
    """Convert text to a slug ID."""
    # Handle special cases
    text_clean = text.replace("C++", "cpp").replace("C#", "csharp")
    slug = re.sub(r"[^a-z0-9]+", "-", text_clean.lower().strip())
    slug = slug.strip("-")
    return f"{prefix}{slug}" if prefix else slug


def yaml_str_representer(dumper, data):
    """Use block style for multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, yaml_str_representer)


def build_entities():
    """Build the complete entity registry from reference documents."""
    entities = {
        "skills": [],
        "domains": [],
        "organizations": [],
        "roles": [],
        "projects": [],
        "compliance": [],
        "patterns": [],
        "tags": [],
    }

    # === SKILLS / TECHNOLOGIES ===
    skills_data = [
        # Languages
        ("Python", "language", "General-purpose programming language"),
        ("JavaScript", "language", "Web programming language"),
        ("TypeScript", "language", "Typed superset of JavaScript"),
        ("Shell", "language", "Shell scripting (Bash/Zsh)"),
        ("C", "language", "Systems programming language"),
        ("C++", "language", "Systems programming language with OOP"),
        ("PL/SQL", "language", "Oracle procedural SQL extension"),
        # Frameworks
        ("FastAPI", "framework", "Modern Python web framework"),
        ("Django", "framework", "Python web framework"),
        ("React", "framework", "JavaScript UI library"),
        ("Redux", "framework", "State management for React"),
        ("React Native", "framework", "Cross-platform mobile framework"),
        ("VueJS", "framework", "Progressive JavaScript framework"),
        ("NuxtJS", "framework", "Vue.js meta-framework"),
        ("RiotJS", "framework", "Simple component-based UI library"),
        ("GraphQL", "framework", "API query language and runtime"),
        ("Serverless Framework", "framework", "Serverless application toolkit"),
        ("Celery", "framework", "Distributed task queue for Python"),
        # Platforms
        ("AWS", "platform", "Amazon Web Services cloud platform"),
        ("AWS Lambda", "platform", "Serverless compute service"),
        ("AWS DynamoDB", "platform", "NoSQL database service"),
        ("AWS SQS", "platform", "Message queuing service"),
        ("AWS EventBridge", "platform", "Serverless event bus"),
        ("AWS Kinesis", "platform", "Real-time data streaming"),
        ("AWS S3", "platform", "Object storage service"),
        ("AWS API Gateway", "platform", "API management service"),
        ("AWS Athena", "platform", "Interactive query service"),
        ("AWS Timestream", "platform", "Time series database"),
        ("AWS RedShift", "platform", "Data warehouse service"),
        ("AWS AppSync", "platform", "Managed GraphQL service"),
        ("AWS GovCloud", "platform", "Government cloud region"),
        ("AWS X-Ray", "platform", "Distributed tracing service"),
        ("AWS CloudWatch", "platform", "Monitoring and observability"),
        ("AWS Powertools", "platform", "Lambda developer toolkit"),
        ("Azure", "platform", "Microsoft cloud platform"),
        ("Digital Ocean", "platform", "Cloud infrastructure provider"),
        ("CloudFlare", "platform", "Edge/CDN platform"),
        # Tools
        ("Kubernetes", "tool", "Container orchestration platform"),
        ("Docker", "tool", "Container runtime and tooling"),
        ("Terraform", "tool", "Infrastructure as Code tool"),
        ("SaltStack", "tool", "Configuration management"),
        ("Ansible", "tool", "Automation and configuration management"),
        ("GitHub Actions", "tool", "CI/CD platform"),
        ("CircleCI", "tool", "CI/CD platform"),
        ("ArgoCD", "tool", "GitOps continuous delivery"),
        ("Jenkins", "tool", "CI/CD automation server"),
        ("Git", "tool", "Distributed version control"),
        ("DataDog", "tool", "Monitoring and analytics platform"),
        ("Prometheus", "tool", "Monitoring and alerting toolkit"),
        ("LogicMonitor", "tool", "Infrastructure monitoring"),
        ("ThousandEyes", "tool", "Network intelligence platform"),
        ("ReportLab", "tool", "PDF generation library for Python"),
        ("Typst", "tool", "Modern typesetting system"),
        ("MistQL", "tool", "Query language for JSON"),
        ("CycloneDX", "tool", "SBOM standard and tooling"),
        ("SPDX", "tool", "Software package data exchange"),
        ("Apache Kafka", "tool", "Distributed event streaming"),
        ("RabbitMQ", "tool", "Message broker"),
        ("Asterisk PBX", "tool", "Open source telephony engine"),
        ("Ceph", "tool", "Distributed storage system"),
        ("GDAL/OGR", "tool", "Geospatial data abstraction library"),
        ("SnapCraft", "tool", "Linux application packaging"),
        ("Ubuntu Core", "tool", "Minimal Ubuntu for IoT/embedded"),
        ("iPXE", "tool", "Network boot firmware"),
        # Libraries
        ("OpenTelemetry", "library", "Observability framework"),
        ("JSON Patch", "library", "JSON document patching standard"),
        # Protocols
        ("SNMP", "protocol", "Network management protocol"),
        ("SIP/IAX", "protocol", "VoIP signaling protocols"),
        ("SMTP", "protocol", "Email transfer protocol"),
        ("HL7/FHIR", "protocol", "Healthcare data exchange standards"),
        ("DICOM", "protocol", "Medical imaging standard"),
        ("Twilio", "platform", "Cloud communications platform"),
        # Databases
        ("PostgreSQL", "database", "Advanced open source RDBMS"),
        ("PostGIS", "database", "Geospatial extension for PostgreSQL"),
        ("SnowflakeDB", "database", "Cloud data warehouse"),
        ("MongoDB", "database", "Document-oriented NoSQL database"),
        ("Redis", "database", "In-memory data store"),
        ("Intersystems IRIS/Cache", "database", "High-performance database"),
        ("Oracle", "database", "Enterprise RDBMS"),
        # Methodologies (as skills)
        ("Prompt Engineering", "methodology", "LLM prompt design and optimization"),
        ("CI/CD", "methodology", "Continuous integration and deployment"),
        ("Infrastructure as Code", "methodology", "Managing infra through code"),
        ("DevSecOps", "methodology", "Security integrated into DevOps"),
        ("Penetration Testing", "methodology", "Security testing methodology"),
        ("Dependency Scanning", "methodology", "Automated vulnerability detection in deps"),
        ("Synthetic Data Generation", "methodology", "Creating artificial test data"),
        ("Machine Learning", "methodology", "Statistical learning systems"),
    ]

    for name, category, description in skills_data:
        entities["skills"].append({
            "id": slugify(name, "skill-"),
            "name": name,
            "category": category,
            "description": description,
        })

    # === DOMAINS ===
    domains_data = [
        ("Healthcare", "Clinical workflows, medication management, patient care"),
        ("Federal/Government", "Government agencies, compliance, public sector"),
        ("Telecommunications", "Telephony, VoIP, network infrastructure"),
        ("IoT/Industrial", "Internet of Things, edge computing, device fleets"),
        ("Security", "Cybersecurity, supply chain security, zero-trust"),
        ("GIS/Geospatial", "Geographic information systems, spatial data"),
        ("Advertising/Media", "Ad tech, VOD, campaign management, analytics"),
        ("Ag-Tech", "Agricultural technology, hydroponics, environmental control"),
        ("Finance/Enterprise", "Financial services, enterprise architecture"),
        ("SaaS/Product", "Software as a Service, product development"),
        ("Telemedicine", "Remote healthcare, radiology, clinical imaging"),
        ("Observability", "System monitoring, telemetry, distributed tracing"),
        ("Edge Computing", "Edge-optimized architectures, hardware security"),
        ("Data Engineering", "Data pipelines, warehousing, analytics"),
    ]

    for name, description in domains_data:
        entities["domains"].append({
            "id": slugify(name, "domain-"),
            "name": name,
            "description": description,
        })

    # === ORGANIZATIONS ===
    orgs_data = [
        ("Arine", "employer", "Healthcare SaaS - clinical decision support", None),
        ("Brute Technologies", "proprietorship", "Sole proprietorship - technical consulting", None),
        ("Adobe", "client", "Enterprise software company", "TekSystems"),
        ("TekSystems", "contractor", "IT staffing and services", None),
        ("Capital Group", "client", "Investment management firm", "Insight Global"),
        ("Insight Global", "contractor", "Staffing and services", None),
        ("Department of Veteran Affairs", "federal_agency", "US federal healthcare agency", "DocMe360"),
        ("DocMe360", "contractor", "Healthcare technology services", None),
        ("Serverless", "client", "Serverless computing company", None),
        ("Taos", "contractor", "IT consulting firm", "IBM Consulting"),
        ("IBM Consulting", "client", "Enterprise consulting", None),
        ("Metify", "employer", "PaaS/edge computing startup", None),
        ("EveryoneSocial", "employer", "Social media SaaS platform", None),
        ("CGI", "contractor", "IT and consulting services", None),
        ("IBM", "client", "Enterprise technology company", None),
        ("AT&T", "client", "Telecommunications company", None),
        ("ABR", "employer", "Environmental research and GIS", None),
        ("Microcom", "employer", "Telecommunications provider", "Sateo"),
        ("Sateo", "employer", "Telecommunications services", None),
        ("Gardyn", "client", "Ag-tech / autonomous hydroponics", None),
        ("Various Organizations", "umbrella", "Multiple client engagements as consultant", None),
    ]

    for name, org_type, description, parent in orgs_data:
        entry = {
            "id": slugify(name, "org-"),
            "name": name,
            "org_type": org_type,
            "description": description,
        }
        if parent:
            entry["parent_org"] = slugify(parent, "org-")
        entities["organizations"].append(entry)

    # === ROLES ===
    roles_data = [
        ("Document Engineering Manager", "org-arine", "manager", "2024-07 to present"),
        ("Full Stack Engineering Team Lead", "org-arine", "lead", "2024-07 to present"),
        ("Strategic Technology Consultant", "org-various-organizations", "senior", "2020-01 to 2024-07"),
        ("Senior Software Engineer", "org-various-organizations", "senior", "2020-01 to 2024-07"),
        ("Principal System Engineer", "org-metify", "principal", "2023-01 to 2023-05"),
        ("Senior Software Development Engineer", "org-everyonesocial", "senior", "2020-12 to 2022-12"),
        ("Platform Engineer", "org-everyonesocial", "senior", "2020-12 to 2022-12"),
        ("Technology Development Consultant", "org-brute-technologies", "senior", "2002-03 to present"),
        ("Senior System Engineer", "org-cgi", "senior", "2016-08 to 2020-12"),
        ("GIS Specialist", "org-abr", "individual_contributor", "2013-04 to 2015-01"),
        ("Telecom Manager", "org-microcom", "manager", "2008-05 to 2012-07"),
        ("Lead System Engineer", "org-microcom", "lead", "2008-05 to 2012-07"),
    ]

    for name, org_id, level, timeframe in roles_data:
        entities["roles"].append({
            "id": slugify(name, "role-"),
            "name": name,
            "organization": org_id,
            "level": level,
            "timeframe": timeframe,
        })

    # === PROJECTS / INITIATIVES ===
    projects_data = [
        ("SBOM Services", "org-adobe", "Enterprise SBOM automation with FastAPI and Python"),
        ("Patient Letter Generation", "org-arine", "Scalable document generation for patient/provider letters"),
        ("Clinical Workflow Portals", "org-arine", "Serverless SaaS portals for medication management"),
        ("Network Observability Transition", "org-capital-group", "Legacy monitoring to Prometheus/OTel architecture"),
        ("Synthetic Data Generation", "org-department-of-veteran-affairs", "Privacy-compliant test environments for ML validation"),
        ("Zero-Trust Data Framework", "org-department-of-veteran-affairs", "Secure data management for federal healthcare"),
        ("OpenTelemetry Libraries", "org-serverless", "Bespoke OTel Python libraries for serverless"),
        ("Microservices Governance", "org-taos", "Dependency scanning and architecture reviews at scale"),
        ("Edge PaaS Provisioning", "org-metify", "Edge-optimized platform provisioning with Secure Boot"),
        ("Serverless Platform Migration", "org-everyonesocial", "Transition to AWS serverless architecture"),
        ("SQS Workflow Engine", "org-everyonesocial", "Custom workflow engine for social media integrations"),
        ("SBOM Lifecycle", "org-everyonesocial", "CycloneDX/SPDX bill of materials implementation"),
        ("Internal Cloud Infrastructure", "org-cgi", "High-availability cloud with SaltStack and Ceph"),
        ("Zero-Trust Access Controls", "org-cgi", "BeyondCorp-style access for telecom network"),
        ("GIS Web Applications", "org-abr", "Custom GIS apps for terrestrial data processing"),
        ("Distributed Telephony Systems", "org-microcom", "Regional Asterisk PBX across Hawaii/Alaska/Idaho"),
        ("Field Data Capture", "org-microcom", "Django web service replacing paper workflows"),
        ("IoT Control Systems", "org-gardyn", "Autonomous hydroponic environment control"),
        ("Telemedicine Imaging", "org-brute-technologies", "DICOM processing for remote clinical work"),
        ("Ad Analytics Pipelines", "org-brute-technologies", "High-volume ingestion and real-time dashboards"),
        ("Review Management System", "org-arine", "Software for clinical review workflows"),
        ("Mailroom/Fax Integration", "org-arine", "Integration of physical mail and fax into digital workflows"),
    ]

    for name, org_id, description in projects_data:
        entities["projects"].append({
            "id": slugify(name, "project-"),
            "name": name,
            "organization": org_id,
            "description": description,
        })

    # === COMPLIANCE / STANDARDS ===
    compliance_data = [
        ("HIPAA", "healthcare", "Health Insurance Portability and Accountability Act"),
        ("CMS", "healthcare", "Centers for Medicare and Medicaid Services regulations"),
        ("Medicare/Medicaid", "healthcare", "Federal healthcare program mandates"),
        ("HL7/FHIR", "healthcare", "Health Level 7 / Fast Healthcare Interoperability Resources"),
        ("SOC I/II", "security", "Service Organization Control audit standards"),
        ("OWASP", "security", "Open Web Application Security Project benchmarks"),
        ("FedRAMP", "federal", "Federal Risk and Authorization Management Program"),
        ("VA/Federal PII/PHI", "federal", "Veterans Affairs data protection regulations"),
        ("Zero-Trust/BeyondCorp", "security", "Zero-trust network architecture model"),
        ("Secure Boot", "supply_chain", "Hardware boot chain verification"),
        ("SBOM Standards", "supply_chain", "Software Bill of Materials (CycloneDX, SPDX)"),
    ]

    for name, scope, description in compliance_data:
        entities["compliance"].append({
            "id": slugify(name, "compliance-"),
            "name": name,
            "scope": scope,
            "description": description,
        })

    # === PATTERNS / PHILOSOPHIES ===
    patterns_data = [
        ("Clean Architecture", "architecture", "Separation of concerns with dependency inversion"),
        ("Domain-Driven Design", "architecture", "Software design centered on business domain models"),
        ("Event-Driven Architecture", "architecture", "Systems communicating through events"),
        ("Microservice Architecture", "architecture", "Decomposed services with independent deployment"),
        ("Serverless Architecture", "architecture", "Cloud-native functions without server management"),
        ("Asynchronous Process Design", "architecture", "Non-blocking concurrent processing patterns"),
        ("Shift-Left Security", "security", "Moving security earlier in the development lifecycle"),
        ("Zero-Trust Architecture", "security", "Never trust, always verify access model"),
        ("DevSecOps", "operations", "Security integrated into development operations"),
        ("Infrastructure as Code", "operations", "Managing infrastructure through declarative code"),
        ("Agentic Engineering", "development", "AI agent-driven development workflows"),
        ("Platform as a Service", "architecture", "Abstracted infrastructure for app deployment"),
        ("Edge-Optimized Architecture", "architecture", "Computing at the network edge"),
        ("Predictive Analytics", "data", "Using data patterns to forecast outcomes"),
        ("Distributed Tracing", "operations", "Tracking requests across distributed systems"),
    ]

    for name, category, description in patterns_data:
        entities["patterns"].append({
            "id": slugify(name, "pattern-"),
            "name": name,
            "category": category,
            "description": description,
        })

    # === TAGS (from pipe-delimited lines in CV) ===
    tags_data = [
        "Document Automation", "Developer Experience", "Advanced Templating Engines",
        "Feature Velocity", "Healthcare Compliance", "Serverless Cloud Architecture",
        "Cross-Functional Leadership", "SDLC Governance", "Enterprise Observability",
        "Telemetry Standardization", "Custom Developer Tooling",
        "Privacy-Preserving Architecture", "Federal Compliance", "Centralized Telemetry",
        "Software Supply Chain Security", "SBOM Automation", "CI/CD Governance",
        "Enterprise Risk Mitigation", "Asynchronous Architecture", "Serverless Ecosystems",
        "Enterprise Architecture Consulting", "Microservices Governance",
        "Cloud Infrastructure", "Edge Computing", "Hardware-Level Security",
        "Platform-as-a-Service", "Continuous Integration/Deployment", "Data Warehousing",
        "Infrastructure Optimization", "High-Concurrency Pipelines", "GraphQL Integrations",
        "Python Packaging", "Remote Radiology", "DICOM Processing", "HIPAA Compliance",
        "Industrial IoT", "Hardware Integration", "Real-Time Telemetry",
        "Big Data Analytics", "Revenue Integrity", "High-Volume Ingestion",
        "Distributed Telephony", "Embedded Linux", "Custom Tooling",
        "Mission-Critical Infrastructure", "Zero-Trust Access", "High-Availability Systems",
        "Complex Data Processing", "Geospatial Architecture", "Workflow Automation",
        "Data Pipeline Engineering", "Distributed Systems", "Voice Operations",
        "Legacy Integration", "Signature Processing", "Operational Analytics",
    ]

    for name in tags_data:
        entities["tags"].append({
            "id": slugify(name, "tag-"),
            "name": name,
        })

    return entities


def build_relationships(entities):
    """Build rich contextual relationships linking entities across dimensions."""
    relationships = []

    # Helper to create a relationship entry
    def rel(subject, predicate, obj, **context):
        entry = {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
        }
        entry["context"] = {k: v for k, v in context.items() if v}
        return entry

    # =========================================================================
    # held_role_at - one per role entity (12 total)
    # =========================================================================
    relationships.append(rel(
        "role-document-engineering-manager", "held_role_at", "org-arine",
        timeframe="2024-07 to present",
        domain="domain-healthcare",
        project=["project-patient-letter-generation", "project-review-management-system", "project-mailroom-fax-integration"],
    ))
    relationships.append(rel(
        "role-full-stack-engineering-team-lead", "held_role_at", "org-arine",
        timeframe="2024-07 to present",
        domain="domain-healthcare",
        project=["project-clinical-workflow-portals"],
    ))
    relationships.append(rel(
        "role-strategic-technology-consultant", "held_role_at", "org-various-organizations",
        timeframe="2020-01 to 2024-07",
        domain="domain-security",
        project=["project-sbom-services", "project-network-observability-transition", "project-synthetic-data-generation"],
    ))
    relationships.append(rel(
        "role-senior-software-engineer", "held_role_at", "org-various-organizations",
        timeframe="2020-01 to 2024-07",
        domain="domain-observability",
        project=["project-opentelemetry-libraries", "project-microservices-governance"],
    ))
    relationships.append(rel(
        "role-principal-system-engineer", "held_role_at", "org-metify",
        timeframe="2023-01 to 2023-05",
        domain="domain-edge-computing",
        project=["project-edge-paas-provisioning"],
    ))
    relationships.append(rel(
        "role-senior-software-development-engineer", "held_role_at", "org-everyonesocial",
        timeframe="2020-12 to 2022-12",
        domain="domain-saas-product",
        project=["project-serverless-platform-migration", "project-sqs-workflow-engine", "project-sbom-lifecycle"],
    ))
    relationships.append(rel(
        "role-platform-engineer", "held_role_at", "org-everyonesocial",
        timeframe="2020-12 to 2022-12",
        domain="domain-saas-product",
        project=["project-serverless-platform-migration"],
    ))
    relationships.append(rel(
        "role-technology-development-consultant", "held_role_at", "org-brute-technologies",
        timeframe="2002-03 to present",
        domain="domain-saas-product",
        project=["project-iot-control-systems", "project-telemedicine-imaging", "project-ad-analytics-pipelines"],
    ))
    relationships.append(rel(
        "role-senior-system-engineer", "held_role_at", "org-cgi",
        timeframe="2016-08 to 2020-12",
        domain="domain-telecommunications",
        project=["project-internal-cloud-infrastructure", "project-zero-trust-access-controls"],
    ))
    relationships.append(rel(
        "role-gis-specialist", "held_role_at", "org-abr",
        timeframe="2013-04 to 2015-01",
        domain="domain-gis-geospatial",
        project=["project-gis-web-applications"],
    ))
    relationships.append(rel(
        "role-telecom-manager", "held_role_at", "org-microcom",
        timeframe="2008-05 to 2012-07",
        domain="domain-telecommunications",
        project=["project-distributed-telephony-systems", "project-field-data-capture"],
    ))
    relationships.append(rel(
        "role-lead-system-engineer", "held_role_at", "org-microcom",
        timeframe="2008-05 to 2012-07",
        domain="domain-telecommunications",
        project=["project-distributed-telephony-systems"],
    ))

    # =========================================================================
    # applied_in_project - skill-to-project relationships
    # =========================================================================
    # SBOM Services (Adobe)
    for sk in ["skill-python", "skill-fastapi", "skill-kubernetes", "skill-git",
               "skill-cyclonedx", "skill-spdx", "skill-ci-cd"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-sbom-services",
            organization="org-adobe",
            role="role-senior-software-engineer",
            domain="domain-security",
            timeframe="2020-01 to 2024-07",
        ))

    # Patient Letter Generation (Arine)
    for sk in ["skill-python", "skill-reportlab", "skill-typst", "skill-mistql",
               "skill-json-patch", "skill-aws-lambda"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-patient-letter-generation",
            organization="org-arine",
            role="role-document-engineering-manager",
            domain="domain-healthcare",
            timeframe="2024-07 to present",
        ))

    # Clinical Workflow Portals (Arine)
    for sk in ["skill-python", "skill-javascript", "skill-typescript", "skill-react",
               "skill-redux", "skill-aws-lambda", "skill-aws-dynamodb", "skill-aws-sqs",
               "skill-aws-api-gateway", "skill-aws-powertools"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-clinical-workflow-portals",
            organization="org-arine",
            role="role-full-stack-engineering-team-lead",
            domain="domain-healthcare",
            timeframe="2024-07 to present",
        ))

    # Review Management System (Arine)
    for sk in ["skill-python", "skill-react", "skill-aws-lambda"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-review-management-system",
            organization="org-arine",
            role="role-document-engineering-manager",
            domain="domain-healthcare",
            timeframe="2024-07 to present",
        ))

    # Mailroom/Fax Integration (Arine)
    for sk in ["skill-python", "skill-aws-lambda", "skill-aws-sqs"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-mailroom-fax-integration",
            organization="org-arine",
            role="role-document-engineering-manager",
            domain="domain-healthcare",
            timeframe="2024-07 to present",
        ))

    # Network Observability Transition (Capital Group)
    for sk in ["skill-prometheus", "skill-opentelemetry", "skill-ansible",
               "skill-python", "skill-infrastructure-as-code"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-network-observability-transition",
            organization="org-capital-group",
            role="role-strategic-technology-consultant",
            domain="domain-observability",
            timeframe="2020-01 to 2024-07",
        ))

    # Synthetic Data Generation (VA)
    for sk in ["skill-python", "skill-aws-govcloud", "skill-synthetic-data-generation",
               "skill-machine-learning"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-synthetic-data-generation",
            organization="org-department-of-veteran-affairs",
            role="role-strategic-technology-consultant",
            domain="domain-federal-government",
            timeframe="2020-01 to 2024-07",
        ))

    # Zero-Trust Data Framework (VA)
    for sk in ["skill-python", "skill-aws-govcloud", "skill-opentelemetry"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-zero-trust-data-framework",
            organization="org-department-of-veteran-affairs",
            role="role-strategic-technology-consultant",
            domain="domain-federal-government",
            timeframe="2020-01 to 2024-07",
        ))

    # OpenTelemetry Libraries (Serverless)
    for sk in ["skill-python", "skill-opentelemetry"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-opentelemetry-libraries",
            organization="org-serverless",
            role="role-senior-software-engineer",
            domain="domain-observability",
            timeframe="2020-01 to 2024-07",
        ))

    # Microservices Governance (Taos)
    for sk in ["skill-python", "skill-aws", "skill-dependency-scanning"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-microservices-governance",
            organization="org-taos",
            role="role-strategic-technology-consultant",
            domain="domain-finance-enterprise",
            timeframe="2020-01 to 2024-07",
        ))

    # Edge PaaS Provisioning (Metify)
    for sk in ["skill-python", "skill-docker", "skill-ci-cd", "skill-ubuntu-core",
               "skill-ipxe", "skill-terraform"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-edge-paas-provisioning",
            organization="org-metify",
            role="role-principal-system-engineer",
            domain="domain-edge-computing",
            timeframe="2023-01 to 2023-05",
        ))

    # Serverless Platform Migration (EveryoneSocial)
    for sk in ["skill-aws-lambda", "skill-aws-dynamodb", "skill-aws-appsync",
               "skill-serverless-framework", "skill-python"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-serverless-platform-migration",
            organization="org-everyonesocial",
            role="role-senior-software-development-engineer",
            domain="domain-saas-product",
            timeframe="2020-12 to 2022-12",
        ))

    # SQS Workflow Engine (EveryoneSocial)
    for sk in ["skill-aws-sqs", "skill-python", "skill-aws-lambda"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-sqs-workflow-engine",
            organization="org-everyonesocial",
            role="role-senior-software-development-engineer",
            domain="domain-saas-product",
            timeframe="2020-12 to 2022-12",
        ))

    # SBOM Lifecycle (EveryoneSocial)
    for sk in ["skill-cyclonedx", "skill-spdx", "skill-python"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-sbom-lifecycle",
            organization="org-everyonesocial",
            role="role-senior-software-development-engineer",
            domain="domain-security",
            timeframe="2020-12 to 2022-12",
        ))

    # Internal Cloud Infrastructure (CGI)
    for sk in ["skill-saltstack", "skill-ceph", "skill-python",
               "skill-infrastructure-as-code"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-internal-cloud-infrastructure",
            organization="org-cgi",
            role="role-senior-system-engineer",
            domain="domain-telecommunications",
            timeframe="2016-08 to 2020-12",
        ))

    # Zero-Trust Access Controls (CGI)
    for sk in ["skill-python", "skill-infrastructure-as-code"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-zero-trust-access-controls",
            organization="org-cgi",
            role="role-senior-system-engineer",
            domain="domain-telecommunications",
            timeframe="2016-08 to 2020-12",
        ))

    # GIS Web Applications (ABR)
    for sk in ["skill-python", "skill-postgresql", "skill-postgis", "skill-gdal-ogr"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-gis-web-applications",
            organization="org-abr",
            role="role-gis-specialist",
            domain="domain-gis-geospatial",
            timeframe="2013-04 to 2015-01",
        ))

    # Distributed Telephony Systems (Microcom)
    for sk in ["skill-asterisk-pbx", "skill-sip-iax", "skill-python"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-distributed-telephony-systems",
            organization="org-microcom",
            role="role-telecom-manager",
            domain="domain-telecommunications",
            timeframe="2008-05 to 2012-07",
        ))

    # Field Data Capture (Microcom)
    for sk in ["skill-django", "skill-python"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-field-data-capture",
            organization="org-microcom",
            role="role-telecom-manager",
            domain="domain-telecommunications",
            timeframe="2008-05 to 2012-07",
        ))

    # IoT Control Systems (Gardyn)
    for sk in ["skill-apache-kafka", "skill-python", "skill-aws"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-iot-control-systems",
            organization="org-gardyn",
            role="role-technology-development-consultant",
            domain="domain-ag-tech",
            timeframe="2002-03 to present",
        ))

    # Telemedicine Imaging (Brute Technologies)
    for sk in ["skill-dicom", "skill-python", "skill-aws-s3", "skill-hl7-fhir"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-telemedicine-imaging",
            organization="org-brute-technologies",
            role="role-technology-development-consultant",
            domain="domain-telemedicine",
            timeframe="2002-03 to present",
        ))

    # Ad Analytics Pipelines (Brute Technologies)
    for sk in ["skill-aws-athena", "skill-python", "skill-aws-kinesis"]:
        relationships.append(rel(
            sk, "applied_in_project", "project-ad-analytics-pipelines",
            organization="org-brute-technologies",
            role="role-technology-development-consultant",
            domain="domain-advertising-media",
            timeframe="2002-03 to present",
        ))

    # =========================================================================
    # used_at - skill-to-org relationships (expanded to cover orphan skills)
    # =========================================================================

    # === ARINE ===
    arine_skills = [
        "skill-python", "skill-javascript", "skill-typescript",
        "skill-react", "skill-redux", "skill-aws-lambda",
        "skill-aws-dynamodb", "skill-aws-sqs", "skill-aws-api-gateway",
        "skill-aws-powertools", "skill-reportlab", "skill-typst",
        "skill-mistql", "skill-json-patch",
    ]
    for sk in arine_skills:
        relationships.append(rel(
            sk, "used_at", "org-arine",
            role="role-full-stack-engineering-team-lead",
            domain="domain-healthcare",
            timeframe="2024-07 to present",
            compliance=["compliance-cms", "compliance-medicare-medicaid", "compliance-hipaa"],
            co_skills=[s for s in arine_skills if s != sk][:5],
        ))

    # === ADOBE / TekSystems ===
    adobe_skills = [
        "skill-python", "skill-fastapi", "skill-kubernetes",
        "skill-git", "skill-cyclonedx", "skill-spdx",
        "skill-ci-cd", "skill-github-actions",
    ]
    for sk in adobe_skills:
        relationships.append(rel(
            sk, "used_at", "org-adobe",
            role="role-senior-software-engineer",
            project="project-sbom-services",
            domain="domain-security",
            timeframe="2020-01 to 2024-07",
            compliance=["compliance-soc-i-ii", "compliance-owasp"],
            co_skills=[s for s in adobe_skills if s != sk][:5],
        ))

    # === CAPITAL GROUP ===
    cg_skills = [
        "skill-prometheus", "skill-opentelemetry", "skill-ansible",
        "skill-python", "skill-infrastructure-as-code",
        "skill-logicmonitor", "skill-thousandeyes", "skill-snmp",
    ]
    for sk in cg_skills:
        relationships.append(rel(
            sk, "used_at", "org-capital-group",
            role="role-strategic-technology-consultant",
            project="project-network-observability-transition",
            domain="domain-observability",
            timeframe="2020-01 to 2024-07",
            co_skills=[s for s in cg_skills if s != sk][:5],
        ))

    # === DEPT OF VA ===
    va_skills = [
        "skill-python", "skill-opentelemetry", "skill-aws-govcloud",
        "skill-synthetic-data-generation", "skill-machine-learning",
    ]
    for sk in va_skills:
        relationships.append(rel(
            sk, "used_at", "org-department-of-veteran-affairs",
            role="role-strategic-technology-consultant",
            domain="domain-federal-government",
            timeframe="2020-01 to 2024-07",
            compliance=["compliance-hipaa", "compliance-fedramp", "compliance-va-federal-pii-phi"],
            co_skills=[s for s in va_skills if s != sk],
        ))

    # === SERVERLESS ===
    relationships.append(rel(
        "skill-opentelemetry", "used_at", "org-serverless",
        role="role-senior-software-engineer",
        project="project-opentelemetry-libraries",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
        co_skills=["skill-python"],
    ))
    relationships.append(rel(
        "skill-python", "used_at", "org-serverless",
        role="role-senior-software-engineer",
        project="project-opentelemetry-libraries",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
        co_skills=["skill-opentelemetry"],
    ))

    # === TAOS / IBM ===
    taos_skills = [
        "skill-python", "skill-aws", "skill-dependency-scanning",
    ]
    for sk in taos_skills:
        relationships.append(rel(
            sk, "used_at", "org-taos",
            role="role-strategic-technology-consultant",
            project="project-microservices-governance",
            domain="domain-finance-enterprise",
            timeframe="2020-01 to 2024-07",
            compliance=["compliance-soc-i-ii", "compliance-owasp"],
            co_skills=[s for s in taos_skills if s != sk],
        ))

    # === METIFY ===
    metify_skills = [
        "skill-python", "skill-docker", "skill-ci-cd",
        "skill-terraform", "skill-ubuntu-core", "skill-ipxe",
    ]
    for sk in metify_skills:
        relationships.append(rel(
            sk, "used_at", "org-metify",
            role="role-principal-system-engineer",
            project="project-edge-paas-provisioning",
            domain="domain-edge-computing",
            timeframe="2023-01 to 2023-05",
            compliance=["compliance-secure-boot"],
            co_skills=[s for s in metify_skills if s != sk][:5],
        ))

    # === EVERYONESOCIAL ===
    es_skills = [
        "skill-python", "skill-react", "skill-react-native",
        "skill-aws-lambda", "skill-aws-dynamodb", "skill-aws-sqs",
        "skill-aws-athena", "skill-aws-timestream", "skill-aws-appsync",
        "skill-serverless-framework", "skill-opentelemetry", "skill-datadog",
        "skill-graphql", "skill-cyclonedx", "skill-spdx",
        "skill-aws-redshift", "skill-aws-kinesis", "skill-aws-eventbridge",
    ]
    for sk in es_skills:
        relationships.append(rel(
            sk, "used_at", "org-everyonesocial",
            role="role-senior-software-development-engineer",
            domain="domain-saas-product",
            timeframe="2020-12 to 2022-12",
            co_skills=[s for s in es_skills if s != sk][:5],
        ))

    # === CGI / IBM / AT&T ===
    cgi_skills = [
        "skill-saltstack", "skill-ceph", "skill-python",
        "skill-infrastructure-as-code", "skill-docker",
        "skill-jenkins", "skill-ansible",
    ]
    for sk in cgi_skills:
        relationships.append(rel(
            sk, "used_at", "org-cgi",
            role="role-senior-system-engineer",
            domain="domain-telecommunications",
            timeframe="2016-08 to 2020-12",
            project="project-internal-cloud-infrastructure",
            co_skills=[s for s in cgi_skills if s != sk][:5],
        ))

    # === ABR ===
    abr_skills = ["skill-python", "skill-postgresql", "skill-postgis", "skill-gdal-ogr"]
    for sk in abr_skills:
        relationships.append(rel(
            sk, "used_at", "org-abr",
            role="role-gis-specialist",
            project="project-gis-web-applications",
            domain="domain-gis-geospatial",
            timeframe="2013-04 to 2015-01",
            co_skills=[s for s in abr_skills if s != sk],
        ))

    # === MICROCOM / SATEO ===
    mic_skills = [
        "skill-python", "skill-django", "skill-asterisk-pbx",
        "skill-sip-iax", "skill-snapcraft", "skill-shell",
    ]
    for sk in mic_skills:
        relationships.append(rel(
            sk, "used_at", "org-microcom",
            role="role-telecom-manager",
            domain="domain-telecommunications",
            timeframe="2008-05 to 2012-07",
            co_skills=[s for s in mic_skills if s != sk][:5],
        ))

    # === BRUTE TECHNOLOGIES (various clients) ===
    brute_skills = [
        "skill-python", "skill-aws", "skill-docker",
        "skill-mongodb", "skill-redis", "skill-celery",
    ]
    for sk in brute_skills:
        relationships.append(rel(
            sk, "used_at", "org-brute-technologies",
            role="role-technology-development-consultant",
            domain="domain-saas-product",
            timeframe="2002-03 to present",
            co_skills=[s for s in brute_skills if s != sk][:5],
        ))

    # === GARDYN ===
    gardyn_skills = ["skill-apache-kafka", "skill-python", "skill-aws"]
    for sk in gardyn_skills:
        relationships.append(rel(
            sk, "used_at", "org-gardyn",
            role="role-technology-development-consultant",
            domain="domain-ag-tech",
            timeframe="2002-03 to present",
            co_skills=[s for s in gardyn_skills if s != sk],
        ))

    # Wire remaining orphan skills into appropriate orgs
    relationships.append(rel(
        "skill-terraform", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-saltstack", "skill-ansible", "skill-docker"],
    ))
    relationships.append(rel(
        "skill-redis", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-python", "skill-aws-lambda"],
    ))
    relationships.append(rel(
        "skill-mongodb", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-python", "skill-graphql"],
    ))
    relationships.append(rel(
        "skill-shell", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-saltstack", "skill-python"],
    ))
    relationships.append(rel(
        "skill-github-actions", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-python", "skill-docker", "skill-ci-cd"],
    ))
    relationships.append(rel(
        "skill-circleci", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-python", "skill-docker", "skill-ci-cd"],
    ))
    relationships.append(rel(
        "skill-argocd", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-kubernetes", "skill-docker"],
    ))
    relationships.append(rel(
        "skill-azure", "used_at", "org-capital-group",
        role="role-strategic-technology-consultant",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
        co_skills=["skill-prometheus", "skill-ansible"],
    ))
    relationships.append(rel(
        "skill-digital-ocean", "used_at", "org-brute-technologies",
        role="role-technology-development-consultant",
        domain="domain-saas-product",
        timeframe="2002-03 to present",
        co_skills=["skill-python", "skill-docker"],
    ))
    relationships.append(rel(
        "skill-cloudflare", "used_at", "org-brute-technologies",
        role="role-technology-development-consultant",
        domain="domain-saas-product",
        timeframe="2002-03 to present",
        co_skills=["skill-python"],
    ))
    relationships.append(rel(
        "skill-vuejs", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-nuxtjs", "skill-javascript"],
    ))
    relationships.append(rel(
        "skill-nuxtjs", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-vuejs", "skill-javascript"],
    ))
    relationships.append(rel(
        "skill-riotjs", "used_at", "org-brute-technologies",
        role="role-technology-development-consultant",
        domain="domain-saas-product",
        timeframe="2002-03 to present",
        co_skills=["skill-javascript"],
    ))
    relationships.append(rel(
        "skill-c", "used_at", "org-microcom",
        role="role-lead-system-engineer",
        domain="domain-telecommunications",
        timeframe="2008-05 to 2012-07",
        co_skills=["skill-cpp", "skill-shell"],
    ))
    relationships.append(rel(
        "skill-cpp", "used_at", "org-microcom",
        role="role-lead-system-engineer",
        domain="domain-telecommunications",
        timeframe="2008-05 to 2012-07",
        co_skills=["skill-c", "skill-shell"],
    ))
    relationships.append(rel(
        "skill-pl-sql", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-python", "skill-oracle"],
    ))
    relationships.append(rel(
        "skill-snowflakedb", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-data-engineering",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-aws-athena", "skill-aws-redshift"],
    ))
    relationships.append(rel(
        "skill-intersystems-iris-cache", "used_at", "org-arine",
        role="role-full-stack-engineering-team-lead",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
        co_skills=["skill-python"],
    ))
    relationships.append(rel(
        "skill-oracle", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-pl-sql", "skill-python"],
    ))
    relationships.append(rel(
        "skill-rabbitmq", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-python", "skill-celery"],
    ))
    relationships.append(rel(
        "skill-smtp", "used_at", "org-arine",
        role="role-document-engineering-manager",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
        co_skills=["skill-python", "skill-aws-sqs"],
    ))
    relationships.append(rel(
        "skill-twilio", "used_at", "org-brute-technologies",
        role="role-technology-development-consultant",
        domain="domain-telecommunications",
        timeframe="2002-03 to present",
        co_skills=["skill-python", "skill-sip-iax"],
    ))
    relationships.append(rel(
        "skill-prompt-engineering", "used_at", "org-arine",
        role="role-document-engineering-manager",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
        co_skills=["skill-python"],
    ))
    relationships.append(rel(
        "skill-penetration-testing", "used_at", "org-cgi",
        role="role-senior-system-engineer",
        domain="domain-security",
        timeframe="2016-08 to 2020-12",
        co_skills=["skill-devsecops"],
    ))
    relationships.append(rel(
        "skill-devsecops", "used_at", "org-adobe",
        role="role-senior-software-engineer",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
        co_skills=["skill-ci-cd", "skill-kubernetes"],
    ))
    relationships.append(rel(
        "skill-aws-x-ray", "used_at", "org-everyonesocial",
        role="role-senior-software-development-engineer",
        domain="domain-observability",
        timeframe="2020-12 to 2022-12",
        co_skills=["skill-opentelemetry", "skill-datadog"],
    ))
    relationships.append(rel(
        "skill-aws-cloudwatch", "used_at", "org-arine",
        role="role-full-stack-engineering-team-lead",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
        co_skills=["skill-aws-lambda", "skill-aws-powertools"],
    ))
    relationships.append(rel(
        "skill-aws-s3", "used_at", "org-department-of-veteran-affairs",
        role="role-strategic-technology-consultant",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
        co_skills=["skill-python", "skill-aws-govcloud"],
    ))

    # =========================================================================
    # part_of - organizational hierarchy
    # =========================================================================
    relationships.append(rel(
        "org-adobe", "part_of", "org-teksystems",
    ))
    relationships.append(rel(
        "org-capital-group", "part_of", "org-insight-global",
    ))
    relationships.append(rel(
        "org-department-of-veteran-affairs", "part_of", "org-docme360",
    ))
    relationships.append(rel(
        "org-taos", "part_of", "org-ibm-consulting",
    ))
    relationships.append(rel(
        "org-microcom", "part_of", "org-sateo",
    ))
    relationships.append(rel(
        "org-ibm", "part_of", "org-cgi",
    ))
    relationships.append(rel(
        "org-at-t", "part_of", "org-cgi",
    ))

    # =========================================================================
    # governed_by - project/org compliance relationships
    # =========================================================================
    relationships.append(rel(
        "project-patient-letter-generation", "governed_by", "compliance-cms",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-patient-letter-generation", "governed_by", "compliance-hipaa",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-clinical-workflow-portals", "governed_by", "compliance-hipaa",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-clinical-workflow-portals", "governed_by", "compliance-cms",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-clinical-workflow-portals", "governed_by", "compliance-medicare-medicaid",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-review-management-system", "governed_by", "compliance-cms",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-mailroom-fax-integration", "governed_by", "compliance-cms",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-sbom-services", "governed_by", "compliance-sbom-standards",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-sbom-services", "governed_by", "compliance-owasp",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-sbom-services", "governed_by", "compliance-soc-i-ii",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-synthetic-data-generation", "governed_by", "compliance-hipaa",
        organization="org-department-of-veteran-affairs",
        domain="domain-healthcare",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-synthetic-data-generation", "governed_by", "compliance-va-federal-pii-phi",
        organization="org-department-of-veteran-affairs",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-zero-trust-data-framework", "governed_by", "compliance-fedramp",
        organization="org-department-of-veteran-affairs",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-zero-trust-data-framework", "governed_by", "compliance-va-federal-pii-phi",
        organization="org-department-of-veteran-affairs",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-microservices-governance", "governed_by", "compliance-soc-i-ii",
        organization="org-taos",
        domain="domain-finance-enterprise",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-microservices-governance", "governed_by", "compliance-owasp",
        organization="org-taos",
        domain="domain-finance-enterprise",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-edge-paas-provisioning", "governed_by", "compliance-secure-boot",
        organization="org-metify",
        domain="domain-edge-computing",
        timeframe="2023-01 to 2023-05",
    ))
    relationships.append(rel(
        "project-sbom-lifecycle", "governed_by", "compliance-sbom-standards",
        organization="org-everyonesocial",
        domain="domain-security",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "project-zero-trust-access-controls", "governed_by", "compliance-zero-trust-beyondcorp",
        organization="org-cgi",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
    ))
    relationships.append(rel(
        "project-telemedicine-imaging", "governed_by", "compliance-hipaa",
        organization="org-brute-technologies",
        domain="domain-telemedicine",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-telemedicine-imaging", "governed_by", "compliance-hl7-fhir",
        organization="org-brute-technologies",
        domain="domain-telemedicine",
        timeframe="2002-03 to present",
    ))

    # =========================================================================
    # implements_pattern - project-to-pattern relationships
    # =========================================================================
    relationships.append(rel(
        "project-patient-letter-generation", "implements_pattern", "pattern-clean-architecture",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-patient-letter-generation", "implements_pattern", "pattern-domain-driven-design",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-clinical-workflow-portals", "implements_pattern", "pattern-serverless-architecture",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-clinical-workflow-portals", "implements_pattern", "pattern-event-driven-architecture",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "project-sbom-services", "implements_pattern", "pattern-shift-left-security",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-sbom-services", "implements_pattern", "pattern-devsecops",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-network-observability-transition", "implements_pattern", "pattern-infrastructure-as-code",
        organization="org-capital-group",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-network-observability-transition", "implements_pattern", "pattern-predictive-analytics",
        organization="org-capital-group",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-network-observability-transition", "implements_pattern", "pattern-distributed-tracing",
        organization="org-capital-group",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-zero-trust-data-framework", "implements_pattern", "pattern-zero-trust-architecture",
        organization="org-department-of-veteran-affairs",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-opentelemetry-libraries", "implements_pattern", "pattern-asynchronous-process-design",
        organization="org-serverless",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-opentelemetry-libraries", "implements_pattern", "pattern-distributed-tracing",
        organization="org-serverless",
        domain="domain-observability",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-microservices-governance", "implements_pattern", "pattern-microservice-architecture",
        organization="org-taos",
        domain="domain-finance-enterprise",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "project-edge-paas-provisioning", "implements_pattern", "pattern-edge-optimized-architecture",
        organization="org-metify",
        domain="domain-edge-computing",
        timeframe="2023-01 to 2023-05",
    ))
    relationships.append(rel(
        "project-edge-paas-provisioning", "implements_pattern", "pattern-platform-as-a-service",
        organization="org-metify",
        domain="domain-edge-computing",
        timeframe="2023-01 to 2023-05",
    ))
    relationships.append(rel(
        "project-serverless-platform-migration", "implements_pattern", "pattern-serverless-architecture",
        organization="org-everyonesocial",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "project-sqs-workflow-engine", "implements_pattern", "pattern-event-driven-architecture",
        organization="org-everyonesocial",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "project-sqs-workflow-engine", "implements_pattern", "pattern-asynchronous-process-design",
        organization="org-everyonesocial",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "project-internal-cloud-infrastructure", "implements_pattern", "pattern-infrastructure-as-code",
        organization="org-cgi",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
    ))
    relationships.append(rel(
        "project-zero-trust-access-controls", "implements_pattern", "pattern-zero-trust-architecture",
        organization="org-cgi",
        domain="domain-telecommunications",
        timeframe="2016-08 to 2020-12",
    ))
    relationships.append(rel(
        "project-distributed-telephony-systems", "implements_pattern", "pattern-distributed-tracing",
        organization="org-microcom",
        domain="domain-telecommunications",
        timeframe="2008-05 to 2012-07",
    ))
    relationships.append(rel(
        "project-iot-control-systems", "implements_pattern", "pattern-event-driven-architecture",
        organization="org-gardyn",
        domain="domain-ag-tech",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-ad-analytics-pipelines", "implements_pattern", "pattern-predictive-analytics",
        organization="org-brute-technologies",
        domain="domain-advertising-media",
        timeframe="2002-03 to present",
    ))

    # =========================================================================
    # operates_in_domain - org/project-to-domain relationships
    # =========================================================================
    relationships.append(rel(
        "org-arine", "operates_in_domain", "domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "org-adobe", "operates_in_domain", "domain-security",
        timeframe="2020-01 to 2024-07",
        compliance=["compliance-soc-i-ii"],
    ))
    relationships.append(rel(
        "org-capital-group", "operates_in_domain", "domain-finance-enterprise",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "org-department-of-veteran-affairs", "operates_in_domain", "domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "org-department-of-veteran-affairs", "operates_in_domain", "domain-healthcare",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "org-metify", "operates_in_domain", "domain-edge-computing",
        timeframe="2023-01 to 2023-05",
    ))
    relationships.append(rel(
        "org-everyonesocial", "operates_in_domain", "domain-saas-product",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "org-cgi", "operates_in_domain", "domain-telecommunications",
        timeframe="2016-08 to 2020-12",
    ))
    relationships.append(rel(
        "org-abr", "operates_in_domain", "domain-gis-geospatial",
        timeframe="2013-04 to 2015-01",
    ))
    relationships.append(rel(
        "org-microcom", "operates_in_domain", "domain-telecommunications",
        timeframe="2008-05 to 2012-07",
    ))
    relationships.append(rel(
        "org-gardyn", "operates_in_domain", "domain-ag-tech",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "org-gardyn", "operates_in_domain", "domain-iot-industrial",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-gis-web-applications", "operates_in_domain", "domain-gis-geospatial",
        organization="org-abr",
        timeframe="2013-04 to 2015-01",
    ))
    relationships.append(rel(
        "project-iot-control-systems", "operates_in_domain", "domain-iot-industrial",
        organization="org-gardyn",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-iot-control-systems", "operates_in_domain", "domain-ag-tech",
        organization="org-gardyn",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-field-data-capture", "operates_in_domain", "domain-telecommunications",
        organization="org-microcom",
        timeframe="2008-05 to 2012-07",
    ))
    relationships.append(rel(
        "project-ad-analytics-pipelines", "operates_in_domain", "domain-advertising-media",
        organization="org-brute-technologies",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-telemedicine-imaging", "operates_in_domain", "domain-telemedicine",
        organization="org-brute-technologies",
        timeframe="2002-03 to present",
    ))
    relationships.append(rel(
        "project-serverless-platform-migration", "operates_in_domain", "domain-saas-product",
        organization="org-everyonesocial",
        timeframe="2020-12 to 2022-12",
    ))

    # =========================================================================
    # co_occurs_with - pattern/compliance co-occurrence
    # =========================================================================
    relationships.append(rel(
        "pattern-shift-left-security", "co_occurs_with", "compliance-sbom-standards",
        organization="org-adobe",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "pattern-zero-trust-architecture", "co_occurs_with", "compliance-fedramp",
        organization="org-department-of-veteran-affairs",
        domain="domain-federal-government",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "pattern-serverless-architecture", "co_occurs_with", "pattern-event-driven-architecture",
        organization="org-everyonesocial",
        domain="domain-saas-product",
        timeframe="2020-12 to 2022-12",
    ))
    relationships.append(rel(
        "pattern-domain-driven-design", "co_occurs_with", "pattern-clean-architecture",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))
    relationships.append(rel(
        "pattern-devsecops", "co_occurs_with", "pattern-shift-left-security",
        domain="domain-security",
        timeframe="2020-01 to 2024-07",
    ))
    relationships.append(rel(
        "pattern-agentic-engineering", "co_occurs_with", "pattern-clean-architecture",
        organization="org-arine",
        domain="domain-healthcare",
        timeframe="2024-07 to present",
    ))

    return relationships


def write_yaml(data, filepath: Path, header: str = ""):
    """Write data to YAML file with optional header comment."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        if header:
            f.write(header)
            f.write("\n\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, width=120, allow_unicode=True)


def main():
    """Main extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract taxonomy from CV reference documents."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview output counts without writing files.",
    )
    args = parser.parse_args()

    print("Extracting taxonomy from reference documents...")

    entities = build_entities()
    relationships = build_relationships(entities)

    # Count entities
    total = sum(len(v) for v in entities.values())
    print(f"  Extracted {total} entities across {len(entities)} categories")
    print(f"  Built {len(relationships)} contextual relationships")

    if args.dry_run:
        print("\n  [DRY RUN] No files written.")
        # Show predicate distribution
        from collections import Counter
        pred_counts = Counter(r["predicate"] for r in relationships)
        print("  Relationship distribution:")
        for pred, count in pred_counts.most_common():
            print(f"    {pred}: {count}")
        return 0

    # Write entities
    entities_header = (
        "# Taxonomy Entities\n"
        "# All entities extracted from CV reference documents, organized by type.\n"
        "# Each entity has a unique slugified ID, name, and type-specific metadata."
    )
    write_yaml(entities, REPO_ROOT / "taxonomy" / "entities.yaml", entities_header)
    print("  Wrote taxonomy/entities.yaml")

    # Write relationships
    rel_header = (
        "# Taxonomy Relationships\n"
        "# Rich contextual relationships (quads) linking entities across multiple dimensions.\n"
        "# Each relationship includes subject, predicate, object, and a context block\n"
        "# with role, project, domain, compliance, timeframe, and co-occurring skills."
    )
    rel_data = {"relationships": relationships}
    write_yaml(rel_data, REPO_ROOT / "taxonomy" / "relationships.yaml", rel_header)
    print("  Wrote taxonomy/relationships.yaml")

    print("Done. Taxonomy artifacts written to taxonomy/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
