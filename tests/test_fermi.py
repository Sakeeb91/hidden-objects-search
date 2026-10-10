import numpy as np
import pandas as pd
import pytest

from hos import fermi


@pytest.fixture(scope="module")
def cat():
    if not fermi.FGL_PATH.exists():
        pytest.skip("4FGL catalog not downloaded")
    return fermi.load_4fgl()


def test_feature_matrix_is_always_finite():
    df = pd.DataFrame({f: [np.inf, -np.inf, np.nan, 1.0] for f in fermi.FEATURES})
    assert np.isfinite(fermi.feature_matrix(df)).all()


def test_classifier_ranks_known_msp_above_known_blazar(cat):
    model, auc = fermi.train_classifier(cat)
    assert auc > 0.9
    # J1023+0038 (transitional redback, class 'lmb' so NOT in the training set) vs
    # 3C 454.3 (FSRQ): an unseen spider must still look more pulsar-like.
    msp = cat[cat["assoc1"] == "PSR J1023+0038"]
    fsrq = cat[cat["assoc1"] == "3C 454.3"]
    assert len(msp) == 1 and len(fsrq) == 1
    assert fermi.p_pulsar(model, msp)[0] > fermi.p_pulsar(model, fsrq)[0]


def test_assoc1_has_no_missing_values(cat):
    assert cat["assoc1"].notna().all()


def test_unassociated_classes_include_unk(cat):
    assert {"", "unk"} <= set(cat["cls"].unique())
