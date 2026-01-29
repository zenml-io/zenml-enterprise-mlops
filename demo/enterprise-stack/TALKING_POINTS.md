# Sales Engineering Talking Points

> Internal notes for the demo. Do not share with customers.

## Context: Zalando

**What we know:**
- Platform team spent last year building Airflow infrastructure
- They're happy with it (no burning pain to solve)
- Evaluating MLOps blueprint - ZenML is one of several choices
- Comparing against "big cloud providers + smaller ones"
- Primary need: Batch inference (batch and real-time separately)
- Integrations needed: Databricks, AWS, Airflow
- ~20 users in POC phase
- Alejandro (lead) won't be live - watching recording later

**What they said explicitly:**
> "I would say focusing on what we discussed last time on the call - batch inference
> primarily (as we're looking for options on batch and real time separately), as well
> as integrations particularly with databricks, aws and airflow"
>
> "Also giving a glimpse on the opportunity on agentic bridging MLOps and LLMOps,
> but focusing mostly on supporting traditional ML at scale"

---

## The Strategy: "Boring Stack, Magical DevEx"

Don't pitch ZenML as replacing anything. Pitch it as the **developer interface**
to their existing heavy infrastructure.

The message: "You built the engine. We're building the steering wheel."

---

## Demo Script

### Opening (2 mins)

**Say:**
> "Thanks for having us. I know you've invested significantly in Airflow and
> Databricks - and you're happy with that foundation. We're not here to replace
> any of that.
>
> What we're going to show you is how ZenML becomes the developer-friendly layer
> on top. Your platform team keeps control of infrastructure. Your data scientists
> get a pure Python experience."

**Show:** The stack diagram from the README

---

### Part 1: The Stack (5 mins)

**Navigate to:** `demo/enterprise-stack/stacks/airflow_databricks_aws.yaml`

**Say:**
> "This is a ZenML stack configured with your exact infrastructure:
> - Airflow as the orchestrator
> - Databricks as the step operator for heavy compute
> - S3 for artifact storage
>
> A platform engineer sets this up once. Data scientists never touch it."

**Show:** Stack registration command

```bash
zenml stack register enterprise-stack \
  --orchestrator airflow \
  --step-operator databricks \
  --artifact-store s3
```

**Key point:**
> "Notice: no Airflow connection strings, no Databricks tokens in the pipeline code.
> That's all in the stack configuration, managed by your platform team."

---

### Part 2: Batch Inference (15 mins)

#### 2A: The ZenML Way (5 mins)

**Navigate to:** `demo/enterprise-stack/pipelines/batch_inference_enterprise.py`

**Say:**
> "Here's a batch inference pipeline. Let me walk through what a data scientist
> writes vs. what actually happens."

**Show the code:**
```python
@step
def load_batch_data() -> pd.DataFrame:
    # Pure Python - load your batch data
    return pd.read_parquet("s3://bucket/batch_data/")

@step
def predict_batch(data: pd.DataFrame, model: ClassifierMixin) -> pd.DataFrame:
    # Pure Python - make predictions
    predictions = model.predict(data)
    return data.assign(predictions=predictions)

@pipeline
def batch_inference_pipeline():
    model = Model(name="my_model", version=ModelStages.PRODUCTION)
    data = load_batch_data()
    predictions = predict_batch(data, model.load_artifact("model"))
    return predictions
```

**Key point:**
> "Look at this code. No Airflow imports. No DAG definitions. No Docker.
> The data scientist stays in pure Python, in their local IDE.
>
> When they run this against the enterprise stack, ZenML:
> 1. Builds the Docker image with their dependencies
> 2. Pushes it to your container registry
> 3. Generates the Airflow DAG
> 4. Submits heavy steps to Databricks
> 5. Tracks all artifacts in S3
> 6. Records complete lineage"

---

#### 2B: Compare to Raw Airflow (5 mins)

**Navigate to:** `demo/enterprise-stack/comparisons/raw_airflow_dag.py`

**Say:**
> "Now let me show you what the same logic looks like if a data scientist
> had to write it directly in Airflow."

**Show the comparison** (side by side if possible)

**Key points:**
> "Count the lines. Count the imports. Count the infrastructure concepts
> a data scientist needs to understand.
>
> With raw Airflow, they need to know:
> - DAG scheduling syntax
> - Operator types
> - XCom for data passing
> - Databricks job submission API
> - Docker/container setup
>
> With ZenML, they need to know:
> - `@step` and `@pipeline`
>
> That's the developer experience difference."

---

#### 2C: Run It (5 mins)

**If live infrastructure available:**
```bash
zenml stack set enterprise-stack
python run.py --pipeline batch_inference
```

**Show:**
- The Airflow UI showing the generated DAG
- The Databricks job running
- The ZenML dashboard with lineage

**If no live infrastructure (dry run):**
- Walk through the dashboard screenshots
- Show example lineage graph

**Key point:**
> "Every prediction in that batch links back to:
> - The exact model version used
> - The training data that created that model
> - The git commit of the training code
> - The Databricks job ID
>
> This is the audit trail your compliance team needs."

---

### Part 3: Agentic Glimpse (10 mins)

**Transition:**
> "Now, you mentioned wanting a glimpse of how this connects to the agentic world.
> Let me show you something that's truly differentiated."

**Navigate to:** `demo/enterprise-stack/agentic/skills_demo.md`

#### 3A: The MCP Connection

**Say:**
> "ZenML has an MCP server that exposes your entire MLOps state to AI agents.
> This isn't a toy - it's a practical interface to complex infrastructure."

**Demo scenario 1: Debugging**
> "Imagine a data scientist's batch job failed at 3am. Instead of SSHing into
> Airflow, checking Databricks logs, they can ask:"

```
"Show me the last failed batch inference run and what step failed"
```

**Show the MCP query returning:**
- Run ID, timestamp, stack used
- Failed step name and error message
- Link to logs

---

#### 3B: Pipeline Modification via Agent

**Demo scenario 2: Adding capabilities**
> "Or imagine they want to add drift detection to their batch pipeline.
> Instead of learning the drift detection library API, they can ask:"

```
"Add a data drift detection step before the predict_batch step
that alerts if drift exceeds 10%"
```

**Show:** The agent generating the step code

**Key point:**
> "This is the bridge between traditional ML and the agentic world.
> The infrastructure stays the same - Airflow, Databricks, AWS.
> But the interface becomes conversational."

---

### Part 4: Wrap Up (5 mins)

**Show:** The ZenML dashboard
- Model versions and stages
- Lineage graph
- Metadata tracking

**Say:**
> "To summarize what we showed:
> 1. Your existing infrastructure stays: Airflow, Databricks, AWS
> 2. Data scientists write pure Python - no infrastructure code
> 3. Platform team controls governance via hooks and stacks
> 4. Complete audit trail for compliance
> 5. AI agents can interface with the whole system via MCP
>
> For the POC, we can help you set up this exact stack in your environment.
> We'd start with batch inference since that's your primary use case."

---

## Q&A Prep

### "How does this compare to Databricks Workflows?"

> "Databricks Workflows is great if you're all-in on Databricks. But what happens
> if part of your team uses SageMaker? Or you acquire a company using Kubeflow?
>
> ZenML gives you one abstraction across all of them. Your pipeline code stays
> the same; you just point it at a different stack."

### "Can we use this incrementally?"

> "Absolutely. You can wrap existing Airflow DAGs one at a time. We're not asking
> for a big-bang migration. Start with one batch inference pipeline, prove the
> value, then expand."

### "What about the 20 users in POC?"

> "Perfect scale for us. Each data scientist writes their own pipelines.
> The platform team defines the stacks and governance hooks once.
> ZenML scales to hundreds of users with proper RBAC (Pro feature)."

### "What about cost?"

> "ZenML Pro is priced per seat. For 20 users, we can discuss specifics offline.
> The OSS version works too but without RBAC and audit logs that enterprise
> compliance typically needs."

---

## Things NOT to Lead With

- ❌ "Replace Airflow" - they're happy with Airflow
- ❌ "AI-native pipelines" - they explicitly said traditional ML focus
- ❌ "Real-time inference" - batch is their stated priority
- ❌ Heavy jargon - Alejandro is watching recording later, keep it accessible
- ❌ Too many features - focus on batch + integrations + glimpse of agentic

---

## Follow-Up Actions

After demo, offer:
1. **POC Setup Call** - Configure Airflow + Databricks + S3 stack in their env
2. **Governance Workshop** - Map their compliance requirements to hooks
3. **Hands-On Session** - Help first DS migrate one batch pipeline
