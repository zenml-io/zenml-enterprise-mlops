# Enterprise Stack Demo: "The Boring Stack, Managed Magically"

> **Audience**: Platform teams evaluating ZenML for enterprise MLOps
> **Focus**: Batch Inference + Airflow + Databricks + AWS
> **Duration**: 30-40 minutes

## The Core Message

**ZenML isn't here to replace your heavy compute or orchestration.**

We're here to make Airflow + Databricks + AWS accessible to your 20+ Data Scientists
without them writing Airflow DAGs manually.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE "BORING" ENTERPRISE STACK                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Data Scientist writes:     Platform Team manages:                  │
│   ┌──────────────────┐       ┌──────────────────────────────────┐   │
│   │  @step           │       │  Airflow Orchestrator            │   │
│   │  def train():    │  ───► │  Databricks Step Operator        │   │
│   │      ...         │       │  S3 Artifact Store               │   │
│   │                  │       │  Docker Images                   │   │
│   └──────────────────┘       │  Governance Hooks                │   │
│                              └──────────────────────────────────┘   │
│                                                                      │
│   Pure Python, Local IDE          Infrastructure abstracted away     │
└─────────────────────────────────────────────────────────────────────┘
```

## Demo Flow

### Part 1: The Setup (5 mins)
**"Meeting you where you are"**

Show the ZenML Stack configured with YOUR infrastructure:
- **Orchestrator**: Airflow (not replacing it)
- **Step Operator**: Databricks (your compute)
- **Artifact Store**: S3 (AWS)

### Part 2: Batch Inference at Scale (15 mins)
**Primary Focus - Alejandro's Request**

Walk through a production batch inference pipeline:
1. Data Scientist stays in Python/Local IDE
2. ZenML handles Docker building, shipping to AWS, triggering Airflow
3. Compare: Python `@step` vs. raw Airflow DAG + Dockerfile

### Part 3: Agentic DevEx Glimpse (10 mins)
**The Differentiator**

Show how an Agent/Skill can:
- "Add drift detection to my batch pipeline"
- "Query metadata for last successful Databricks run"
- Bridge the gap between human and complex infrastructure

### Part 4: Governance & Conclusion (5 mins)
- Dashboard walkthrough (lineage tracking)
- Offer to set up this exact stack in POC environment

---

## Running This Demo

### Prerequisites

```bash
# Ensure you have the required integrations
pip install "zenml[airflow,databricks,s3]"
zenml integration install airflow databricks s3
```

### Option A: With Real Infrastructure

```bash
# 1. Deploy the enterprise stack via Terraform
cd governance/stacks/terraform/enterprise-airflow-databricks
terraform init && terraform apply

# 2. Register the stack
python demo/enterprise-stack/register_stack.py

# 3. Run the batch inference demo
python demo/enterprise-stack/run_demo.py
```

### Option B: Simulated Demo (No Infrastructure)

```bash
# Walk through the code and concepts without running
python demo/enterprise-stack/run_demo.py --dry-run
```

---

## Files in This Demo

```
demo/enterprise-stack/
├── README.md                    # This file
├── run_demo.py                  # Interactive demo runner
├── register_stack.py            # Stack registration helper
├── TALKING_POINTS.md            # Sales engineering notes
│
├── stacks/
│   └── airflow_databricks_aws.yaml   # Stack configuration
│
├── pipelines/
│   └── batch_inference_enterprise.py # Batch inference for enterprise stack
│
├── comparisons/
│   ├── raw_airflow_dag.py       # What they'd write WITHOUT ZenML
│   └── zenml_pipeline.py        # Same logic WITH ZenML
│
└── agentic/
    ├── skills_demo.md           # Agent/Skills demo script
    └── mcp_queries.md           # Example MCP queries
```

---

## Key Differentiators to Highlight

### 1. "We're Not Replacing Airflow"
> "Your platform team invested a year building Airflow infrastructure.
> We're not asking you to throw that away. We're putting a developer-friendly
> layer on top."

### 2. "Data Scientists Stay in Python"
> "Look at this batch inference pipeline. Pure Python. No Airflow imports,
> no DAG definitions, no Dockerfile writing. The Data Scientist doesn't need
> to know Airflow exists."

### 3. "Swap Without Code Changes"
> "If next year you move from Databricks to SageMaker, or Airflow to Kubernetes,
> your pipeline code stays identical. You just change the stack."

### 4. "Complete Lineage Across Systems"
> "Every batch prediction links back to: the model version, the training data,
> the git commit, the Databricks job ID. Full audit trail."

### 5. "Agent as Infrastructure Interface"
> "Your DS doesn't need to SSH into Airflow or navigate Databricks UI.
> They can ask: 'Why did my last batch job fail?' and get the answer."

---

## Addressing Common Questions

### "Why not just use Airflow directly?"
Airflow is a backend engine; ZenML is the frontend for your Data Scientists.
We decouple the logic from the infrastructure. Your platform team manages the
Airflow stack; your DS team just writes `@step`.

### "Why ZenML vs. Databricks Workflows?"
We're truly agnostic. If you move from Databricks to different compute later,
or swap Airflow for something else, your code doesn't change. You own the abstraction.

### "How does this scale to 20+ users?"
Each DS writes their pipeline in Python. The platform team defines governance hooks
that automatically apply. No manual DAG review needed - ZenML enforces standards.

### "What about real-time inference?"
We support that too (Pipeline Deployments). But since batch is your primary
use case, let's nail that first. Real-time can be a follow-up conversation.

---

## Next Steps After Demo

1. **POC Setup**: We can help configure this exact stack (Airflow + Databricks + S3)
   in your environment

2. **Governance Workshop**: Walk through how hooks enforce your specific compliance
   requirements

3. **Migration Path**: Show how to wrap existing Airflow DAGs incrementally

---

## Contact

For questions about this demo or to schedule a POC setup session:
- [Your contact info]
