"""Champion/Challenger Batch Inference Pipeline.

This pipeline demonstrates the champion/challenger pattern for safe model rollouts:
- Runs inference with both the current production model (champion) and a staging
  candidate (challenger)
- Compares predictions and metrics side-by-side
- Enables data-driven decisions before promoting challenger to production

Use Cases:
- A/B testing models before full production rollout
- Shadow mode testing where challenger predictions are logged but not served
- Gradual rollout with configurable traffic split

Example:
    python run.py --pipeline champion_challenger
"""

from typing import Annotated

import pandas as pd
from zenml import Model, get_step_context, pipeline, step
from zenml.enums import ModelStages

MODEL_NAME = "breast_cancer_classifier"


@step
def load_inference_data() -> Annotated[pd.DataFrame, "inference_data"]:
    """Load data for inference comparison.

    In production, this would load from BigQuery, GCS, or another data source.
    """
    from sklearn.datasets import make_classification

    X, _ = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=10,
        n_redundant=5,
        random_state=42,
    )

    feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    return pd.DataFrame(X, columns=feature_names)


@step
def predict_with_model(
    data: pd.DataFrame,
    model_stage: str,
) -> Annotated[pd.DataFrame, "predictions"]:
    """Run predictions using a model from a specific stage.

    Args:
        data: Input features for prediction
        model_stage: Which model stage to use ("production" or "staging")
    """
    context = get_step_context()

    # Load model from the specified stage
    if model_stage == "production":
        model_version = context.model
    else:
        # Load challenger from staging
        from zenml.client import Client

        client = Client()
        try:
            staging_mv = client.get_model_version(
                model_name_or_id=MODEL_NAME,
                model_version_name_or_number_or_id=ModelStages.STAGING,
            )
            model_version = staging_mv
        except KeyError:
            context.logger.warning("No staging model found, using production for both")
            model_version = context.model

    # Load artifacts
    model_artifact = model_version.get_artifact("sklearn_classifier")
    scaler_artifact = model_version.get_artifact("scaler")

    if model_artifact is None:
        raise ValueError(f"No model artifact found for stage: {model_stage}")

    model = model_artifact.load()
    scaler = scaler_artifact.load() if scaler_artifact else None

    # Preprocess and predict
    X = data.copy()
    if scaler is not None:
        X = pd.DataFrame(scaler.transform(X), columns=data.columns)

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    results = pd.DataFrame(
        {
            "prediction": predictions,
            "probability": probabilities,
            "model_stage": model_stage,
            "model_version": str(model_version.number),
        }
    )

    return results


@step
def compare_predictions(
    champion_predictions: pd.DataFrame,
    challenger_predictions: pd.DataFrame,
    inference_data: pd.DataFrame,
) -> Annotated[dict, "comparison_metrics"]:
    """Compare champion and challenger model predictions.

    Calculates agreement metrics and flags cases where models disagree.
    """
    comparison = {
        "champion_version": champion_predictions["model_version"].iloc[0],
        "challenger_version": challenger_predictions["model_version"].iloc[0],
        "total_samples": len(inference_data),
        "agreement_rate": (
            champion_predictions["prediction"].values
            == challenger_predictions["prediction"].values
        ).mean(),
        "champion_positive_rate": champion_predictions["prediction"].mean(),
        "challenger_positive_rate": challenger_predictions["prediction"].mean(),
        "avg_probability_diff": abs(
            champion_predictions["probability"].values
            - challenger_predictions["probability"].values
        ).mean(),
        "max_probability_diff": abs(
            champion_predictions["probability"].values
            - challenger_predictions["probability"].values
        ).max(),
    }

    # Log comparison to Model Control Plane
    context = get_step_context()
    context.model.log_metadata({"champion_challenger_comparison": comparison})

    return comparison


@step
def generate_comparison_report(
    comparison_metrics: dict,
) -> Annotated[str, "comparison_report"]:
    """Generate a human-readable comparison report.

    This report helps stakeholders decide whether to promote the challenger.
    """
    report = f"""
# Champion vs Challenger Model Comparison Report

## Model Versions
- **Champion (Production)**: v{comparison_metrics["champion_version"]}
- **Challenger (Staging)**: v{comparison_metrics["challenger_version"]}

## Prediction Agreement
- **Total Samples**: {comparison_metrics["total_samples"]:,}
- **Agreement Rate**: {comparison_metrics["agreement_rate"]:.2%}
- **Disagreement Rate**: {1 - comparison_metrics["agreement_rate"]:.2%}

## Prediction Distribution
- **Champion Positive Rate**: {comparison_metrics["champion_positive_rate"]:.2%}
- **Challenger Positive Rate**: {comparison_metrics["challenger_positive_rate"]:.2%}

## Probability Calibration
- **Average Probability Difference**: {comparison_metrics["avg_probability_diff"]:.4f}
- **Maximum Probability Difference**: {comparison_metrics["max_probability_diff"]:.4f}

## Recommendation
"""

    agreement = comparison_metrics["agreement_rate"]
    prob_diff = comparison_metrics["avg_probability_diff"]

    if agreement >= 0.95 and prob_diff < 0.05:
        report += """
**SAFE TO PROMOTE**: Models are highly aligned. Challenger can likely be
promoted to production with minimal risk.
"""
    elif agreement >= 0.85:
        report += """
**REVIEW RECOMMENDED**: Models show reasonable agreement but some divergence.
Review disagreement cases before promotion.
"""
    else:
        report += """
**CAUTION**: Significant prediction differences detected. Investigate root
cause before considering promotion. Consider:
- Feature drift between training and inference data
- Model architecture differences
- Training data differences
"""

    return report


@pipeline(
    model=Model(
        name=MODEL_NAME,
        version=ModelStages.PRODUCTION,
    ),
)
def champion_challenger_pipeline() -> str:
    """Run champion/challenger comparison for safe model rollouts.

    This pipeline:
    1. Loads inference data
    2. Runs predictions with production model (champion)
    3. Runs predictions with staging model (challenger)
    4. Compares predictions and generates report

    Returns:
        Comparison report with promotion recommendation
    """
    # Load data
    inference_data = load_inference_data()

    # Run both models
    champion_predictions = predict_with_model(
        data=inference_data,
        model_stage="production",
        id="champion_predict",
    )

    challenger_predictions = predict_with_model(
        data=inference_data,
        model_stage="staging",
        id="challenger_predict",
    )

    # Compare and report
    comparison_metrics = compare_predictions(
        champion_predictions=champion_predictions,
        challenger_predictions=challenger_predictions,
        inference_data=inference_data,
    )

    report = generate_comparison_report(
        comparison_metrics=comparison_metrics,
    )

    return report
