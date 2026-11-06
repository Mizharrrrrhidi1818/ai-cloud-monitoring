
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    ROOT / "models"
    / "vps_isolation_forest_candidate.joblib"
)

FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
]


class TestVPSModelCompatibility(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.artifact = joblib.load(MODEL_PATH)
        cls.model = cls.artifact["model"]
        cls.features = cls.artifact["features"]

    def test_model_exists(self):
        self.assertTrue(MODEL_PATH.exists())

    def test_feature_names(self):
        self.assertEqual(self.features, FEATURES)

    def test_model_has_predict(self):
        self.assertTrue(
            callable(getattr(self.model, "predict", None))
        )

    def test_model_has_decision_function(self):
        self.assertTrue(
            callable(
                getattr(self.model, "decision_function", None)
            )
        )

    def test_prediction_output(self):
        samples = pd.DataFrame([
            [3.0, 58.0, 46.8],
            [95.0, 95.0, 98.0],
        ], columns=self.features)

        predictions = self.model.predict(samples)

        self.assertEqual(len(predictions), 2)

        self.assertTrue(
            np.isin(predictions, [-1, 1]).all()
        )

    def test_score_output(self):
        samples = pd.DataFrame([
            [3.0, 58.0, 46.8],
            [95.0, 95.0, 98.0],
        ], columns=self.features)

        scores = self.model.decision_function(samples)

        self.assertEqual(len(scores), 2)
        self.assertTrue(np.isfinite(scores).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
