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
        -d '{"parameters": {"patient_data": {"mean_radius": 14.0, "mean_texture": 19.0, ...}}}'

Uses breast cancer dataset features for demo. See PatientData model for all fields.
"""

from typing import Annotated, Any

from pydantic import BaseModel
from zenml import Model, get_step_context, pipeline, step
from zenml.enums import ModelStages


class PatientData(BaseModel):
    """Patient data for risk prediction.

    This Pydantic model defines the API contract for the deployed service.
    Uses key features from the breast cancer dataset for the demo.
    """

    mean_radius: float = 14.0
    mean_texture: float = 19.0
    mean_perimeter: float = 92.0
    mean_area: float = 655.0
    mean_smoothness: float = 0.096
    mean_compactness: float = 0.104
    mean_concavity: float = 0.088
    mean_concave_points: float = 0.049
    mean_symmetry: float = 0.181
    mean_fractal_dimension: float = 0.063
    # Remaining 20 features with defaults (for full model compatibility)
    radius_error: float = 0.4
    texture_error: float = 1.2
    perimeter_error: float = 2.9
    area_error: float = 40.0
    smoothness_error: float = 0.007
    compactness_error: float = 0.025
    concavity_error: float = 0.032
    concave_points_error: float = 0.012
    symmetry_error: float = 0.021
    fractal_dimension_error: float = 0.004
    worst_radius: float = 16.0
    worst_texture: float = 25.0
    worst_perimeter: float = 107.0
    worst_area: float = 881.0
    worst_smoothness: float = 0.132
    worst_compactness: float = 0.254
    worst_concavity: float = 0.272
    worst_concave_points: float = 0.115
    worst_symmetry: float = 0.290
    worst_fractal_dimension: float = 0.084


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
        model_name_or_id="breast_cancer_classifier",
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

    Extracts features in the correct order to match training data.
    """
    # Feature order must match sklearn breast_cancer dataset
    feature_order = [
        "mean_radius",
        "mean_texture",
        "mean_perimeter",
        "mean_area",
        "mean_smoothness",
        "mean_compactness",
        "mean_concavity",
        "mean_concave_points",
        "mean_symmetry",
        "mean_fractal_dimension",
        "radius_error",
        "texture_error",
        "perimeter_error",
        "area_error",
        "smoothness_error",
        "compactness_error",
        "concavity_error",
        "concave_points_error",
        "symmetry_error",
        "fractal_dimension_error",
        "worst_radius",
        "worst_texture",
        "worst_perimeter",
        "worst_area",
        "worst_smoothness",
        "worst_compactness",
        "worst_concavity",
        "worst_concave_points",
        "worst_symmetry",
        "worst_fractal_dimension",
    ]

    raw = patient_data.model_dump()
    features = [raw[f] for f in feature_order]

    return {
        "features": features,
        "raw": raw,
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

    # Load model and scaler directly from Model Control Plane
    client = Client()
    model_version = client.get_model_version(
        model_name_or_id="breast_cancer_classifier",
        model_version_name_or_number_or_id=ModelStages.PRODUCTION,
    )

    model_artifact = model_version.get_artifact("sklearn_classifier")
    scaler_artifact = model_version.get_artifact("scaler")
    if model_artifact is None:
        raise RuntimeError("No production model found")

    model = model_artifact.load()
    scaler = scaler_artifact.load() if scaler_artifact else None
    version = str(model_version.number)

    # Make prediction - apply scaler first if available
    features = np.array(processed_features["features"]).reshape(1, -1)
    if scaler is not None:
        features = scaler.transform(features)
    prediction = int(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0, 1])

    # Determine risk level
    # Note: probability is P(benign), so low probability = high risk
    if probability > 0.7:
        risk_level = "LOW"
    elif probability > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # Simple feature importance explanation
    raw_data = processed_features["raw"]
    explanation = {
        "top_risk_factors": [],
        "protective_factors": [],
    }

    # Heuristic explanations based on breast cancer risk factors
    # In production, use SHAP/LIME for accurate explanations
    if raw_data.get("mean_radius", 0) > 15:
        explanation["top_risk_factors"].append("Large mean radius")
    if raw_data.get("mean_concavity", 0) > 0.1:
        explanation["top_risk_factors"].append("High concavity")
    if raw_data.get("worst_radius", 0) > 18:
        explanation["top_risk_factors"].append("Large worst radius")
    if raw_data.get("worst_concave_points", 0) > 0.15:
        explanation["top_risk_factors"].append("High worst concave points")

    if raw_data.get("mean_smoothness", 0) < 0.09:
        explanation["protective_factors"].append("Low smoothness")

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
        name="breast_cancer_classifier",
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
            model_name_or_id="breast_cancer_classifier",
            model_version_name_or_number_or_id=ModelStages.PRODUCTION,
        )
        return {
            "status": "healthy",
            "model": "breast_cancer_classifier",
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
