"""Real-Time Inference Pipeline Deployment.

This pipeline demonstrates ZenML's Pipeline Deployments feature for real-time
model serving. Instead of batch processing, this pipeline runs as a long-lived
HTTP service that can be invoked on-demand.

Pipeline Deployments:
- Deploy pipelines as HTTP services (not just batch jobs)
- Cloud Run, Docker, or local backends
- Full pipeline logic per request (preprocessing, inference, postprocessing)
- Built-in auth, CORS, custom endpoints

Why Pipeline Deployments over Model Deployers (Seldon/KServe)?
- More flexible: Add business logic, guardrails, A/B routing
- More customizable: Full ASGI app with middleware hooks
- More features: Serve UIs, dashboards alongside API

Example:
    # Deploy to local Docker
    zenml pipeline deploy src.pipelines.realtime_inference.inference_service \\
        --name readmission-api

    # Deploy to Cloud Run (requires deployer stack component)
    zenml deployer register cloudrun --flavor=gcp_cloud_run
    zenml stack update -d cloudrun
    zenml pipeline deploy src.pipelines.realtime_inference.inference_service \\
        --name readmission-api

    # Invoke the deployed service
    curl -X POST http://localhost:8000/invoke \\
        -H "Content-Type: application/json" \\
        -d '{"parameters": {"patient_data": {"age": 65, "num_procedures": 3}}}'
"""

from typing import Annotated, Any

from pydantic import BaseModel
from zenml import Model, get_step_context, pipeline, step
from zenml.enums import ModelStages


class PatientData(BaseModel):
    """Patient data for readmission prediction.

    This Pydantic model defines the API contract for the deployed service.
    Features match the diabetes dataset used for training.
    """

    age: float = 0.0  # Age (normalized)
    sex: float = 0.0  # Sex (normalized)
    bmi: float = 0.0  # Body mass index (normalized)
    bp: float = 0.0  # Average blood pressure (normalized)
    s1: float = 0.0  # tc, total serum cholesterol (normalized)
    s2: float = 0.0  # ldl, low-density lipoproteins (normalized)
    s3: float = 0.0  # hdl, high-density lipoproteins (normalized)
    s4: float = 0.0  # tch, total cholesterol / HDL (normalized)
    s5: float = 0.0  # ltg, log of serum triglycerides (normalized)
    s6: float = 0.0  # glu, blood sugar level (normalized)


class PredictionResult(BaseModel):
    """Prediction result returned by the service."""

    patient_id: str
    prediction: int
    probability: float
    risk_level: str
    model_version: str
    explanation: dict


def load_model_artifacts():
    """Initialize model artifacts when deployment starts.

    This runs once at deployment startup, not per request.
    Returns artifacts to be shared across all requests.
    """
    from zenml.client import Client

    client = Client()

    # Load production model
    model_version = client.get_model_version(
        model_name_or_id="patient_readmission_predictor",
        model_version_name_or_number_or_id=ModelStages.PRODUCTION,
    )

    model_artifact = model_version.get_artifact("sklearn_classifier")
    scaler_artifact = model_version.get_artifact("scaler")

    if model_artifact is None:
        raise RuntimeError("No production model found")

    return {
        "model": model_artifact.load(),
        "scaler": scaler_artifact.load() if scaler_artifact else None,
        "version": str(model_version.number),
    }


def cleanup_model_artifacts(artifacts: dict | None = None):
    """Cleanup when deployment stops."""
    del artifacts  # No cleanup needed for sklearn models


@step
def preprocess_request(
    patient_data: PatientData,
) -> Annotated[dict, "processed_features"]:
    """Preprocess incoming patient data.

    For this demo, we pass the raw features directly since the training
    data uses different features (diabetes dataset). In production,
    you would apply the same scaler used during training.
    """
    # Return raw features as a list for prediction
    return {
        "features": list(patient_data.model_dump().values()),
        "raw": patient_data.model_dump(),
    }


@step
def predict(
    processed_features: dict,
) -> Annotated[PredictionResult, "prediction"]:
    """Run inference using the loaded production model."""
    import uuid

    import numpy as np
    from zenml.client import Client
    from zenml.enums import ModelStages

    # Load model directly from Model Control Plane
    client = Client()
    model_version = client.get_model_version(
        model_name_or_id="patient_readmission_predictor",
        model_version_name_or_number_or_id=ModelStages.PRODUCTION,
    )

    model_artifact = model_version.get_artifact("sklearn_classifier")
    if model_artifact is None:
        raise RuntimeError("No production model found")

    model = model_artifact.load()
    version = str(model_version.number)

    # Make prediction
    features = np.array(processed_features["features"]).reshape(1, -1)
    prediction = int(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0, 1])

    # Determine risk level
    if probability < 0.3:
        risk_level = "LOW"
    elif probability < 0.6:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # Simple feature importance explanation
    raw_data = processed_features["raw"]
    explanation = {
        "top_risk_factors": [],
        "protective_factors": [],
    }

    # Heuristic explanations based on diabetes risk factors
    # In production, use SHAP/LIME for accurate explanations
    if raw_data.get("bmi", 0) > 0.05:
        explanation["top_risk_factors"].append("Elevated BMI")
    if raw_data.get("bp", 0) > 0.05:
        explanation["top_risk_factors"].append("High blood pressure")
    if raw_data.get("s5", 0) > 0.05:  # log serum triglycerides
        explanation["top_risk_factors"].append("Elevated triglycerides")
    if raw_data.get("s6", 0) > 0.05:  # blood sugar
        explanation["top_risk_factors"].append("Elevated blood sugar")

    if raw_data.get("s3", 0) > 0.05:  # HDL
        explanation["protective_factors"].append("Good HDL cholesterol")

    return PredictionResult(
        patient_id=str(uuid.uuid4())[:8],
        prediction=prediction,
        probability=round(probability, 4),
        risk_level=risk_level,
        model_version=version,
        explanation=explanation,
    )


@pipeline(
    model=Model(
        name="patient_readmission_predictor",
        version=ModelStages.PRODUCTION,
    ),
)
def inference_service(
    patient_data: PatientData = PatientData(),
) -> PredictionResult:
    """Real-time readmission prediction service.

    This pipeline is designed to be deployed as an HTTP service.
    Each HTTP request triggers a full pipeline run.

    Args:
        patient_data: Patient features for prediction

    Returns:
        Prediction result with risk level and explanation

    Deploy with:
        zenml pipeline deploy src.pipelines.realtime_inference.inference_service \\
            --name readmission-api

    Invoke with:
        curl -X POST http://localhost:8000/invoke \\
            -H "Content-Type: application/json" \\
            -d '{"parameters": {"patient_data": {"age": 72, "num_inpatient": 3}}}'
    """
    processed = preprocess_request(patient_data=patient_data)
    result = predict(processed_features=processed)
    return result


# Optional: Custom health check endpoint
async def health_check() -> dict[str, Any]:
    """Custom health check for the deployed service."""
    from zenml.client import Client

    client = Client()
    try:
        # Verify we can access the model
        mv = client.get_model_version(
            model_name_or_id="patient_readmission_predictor",
            model_version_name_or_number_or_id=ModelStages.PRODUCTION,
        )
        return {
            "status": "healthy",
            "model": "patient_readmission_predictor",
            "version": str(mv.number),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Deployment with custom endpoints (for advanced use cases)
# from zenml.config import DeploymentSettings, EndpointSpec, EndpointMethod
#
# inference_service_with_health = inference_service.with_options(
#     settings={
#         "deployment": DeploymentSettings(
#             custom_endpoints=[
#                 EndpointSpec(
#                     path="/health",
#                     method=EndpointMethod.GET,
#                     handler=health_check,
#                     auth_required=False,
#                 ),
#             ],
#         ),
#     }
# )
