# Apache Software License 2.0
#
# Copyright (c) ZenML GmbH 2026. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example shared materializer for DataFrames with enhanced metadata tracking.

This demonstrates how the platform team can create shared materializers
that all data science teams use, ensuring consistent metadata tracking.
"""

import os
from typing import Any, ClassVar, Type

import pandas as pd
from zenml.enums import ArtifactType
from zenml.io import fileio
from zenml.materializers.base_materializer import BaseMaterializer


class EnhancedDataFrameMaterializer(BaseMaterializer):
    """Materializer for pandas DataFrames with governance metadata.

    This materializer extends the default DataFrame handling to include:
    - Row and column counts
    - Memory usage
    - Column types
    - Missing value statistics
    - Data quality metrics

    Usage:
        from governance.materializers import EnhancedDataFrameMaterializer

        @step(output_materializers=EnhancedDataFrameMaterializer)
        def load_data() -> pd.DataFrame:
            return pd.read_csv("data.csv")
    """

    ASSOCIATED_TYPES: ClassVar[tuple[Type[Any], ...]] = (pd.DataFrame,)
    ASSOCIATED_ARTIFACT_TYPE: ClassVar[ArtifactType] = ArtifactType.DATA

    def load(self, data_type: Type[pd.DataFrame]) -> pd.DataFrame:
        """Load a DataFrame from the artifact store.

        Args:
            data_type: The type of the data to load.

        Returns:
            The loaded DataFrame.
        """
        with fileio.open(os.path.join(self.uri, "data.parquet"), "rb") as f:
            return pd.read_parquet(f)

    def save(self, df: pd.DataFrame) -> None:
        """Save a DataFrame to the artifact store with governance metadata.

        Args:
            df: The DataFrame to save.
        """
        # Save the actual data
        with fileio.open(os.path.join(self.uri, "data.parquet"), "wb") as f:
            df.to_parquet(f, index=False)

        # Save governance metadata
        metadata = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "memory_bytes": df.memory_usage(deep=True).sum(),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
        }

        # Platform governance: log metadata
        self.save_visualizations(metadata)
