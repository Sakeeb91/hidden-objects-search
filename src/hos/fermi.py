"""Fermi-LAT 4FGL-DR4 catalog access and a pulsar-likeness classifier.

Pulsars have curved (log-parabola / cutoff) spectra peaking near 1 GeV and steady flux;
blazars are flatter power laws and variable. A random forest trained on associated
sources (pulsars vs AGN) scores the unassociated ones. Galactic latitude is deliberately
NOT a feature, so the score does not bake in a sky-position selection.
"""
import numpy as np
import pandas as pd
from astropy.table import Table

from hos.archives import fetch_url
from hos.paths import DATA

FGL_URL = "https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/gll_psc_v35.fit"
FGL_PATH = DATA / "catalogs" / "gll_psc_v35.fit"

PSR_CLASSES = {"psr", "msp"}
AGN_CLASSES = {"bll", "fsrq", "bcu", "agn", "css", "rdg", "nlsy1", "ssrq", "sey"}
UNASSOC_CLASSES = {"", "unk"}

FEATURES = ["lp_beta", "lp_sigcurv", "log_epeak", "pl_index", "lp_index",
            "log_varindex", "frac_var", "hr12", "hr23", "hr34", "hr45", "hr56"]


def load_4fgl() -> pd.DataFrame:
    """One row per source with the columns this project uses (lower-case names)."""
    fetch_url(FGL_URL, FGL_PATH)
    t = Table.read(FGL_PATH, hdu=1)
    band = np.array(t["Flux_Band"], dtype=float)  # 8 bands, 50 MeV - 1 TeV
    df = pd.DataFrame({
        "name": np.char.strip(t["Source_Name"].astype(str)),
        "ra": np.array(t["RAJ2000"], dtype=float),
        "dec": np.array(t["DEJ2000"], dtype=float),
        "glat": np.array(t["GLAT"], dtype=float),
        "a95": np.array(t["Conf_95_SemiMajor"], dtype=float),
        "b95": np.array(t["Conf_95_SemiMinor"], dtype=float),
        "pa95": np.array(t["Conf_95_PosAng"], dtype=float),
        "data_release": np.array(t["DataRelease"], dtype=int),
        "flags": np.array(t["Flags"], dtype=int),
        "signif": np.array(t["Signif_Avg"], dtype=float),
        "cls": np.char.strip(np.char.lower(t["CLASS1"].astype(str))),
        "assoc1": np.char.strip(t["ASSOC1"].astype(str)),
        "lp_beta": np.array(t["LP_beta"], dtype=float),
        "lp_sigcurv": np.array(t["LP_SigCurv"], dtype=float),
        "log_epeak": np.log10(np.clip(np.array(t["LP_EPeak"], dtype=float), 1, None)),
        "pl_index": np.array(t["PL_Index"], dtype=float),
        "lp_index": np.array(t["LP_Index"], dtype=float),
        "log_varindex": np.log10(np.clip(np.array(t["Variability_Index"], dtype=float), 1e-3, None)),
        "frac_var": np.array(t["Frac_Variability"], dtype=float),
    })
    # Hardness ratios between adjacent bands 2..7 (100 MeV - 100 GeV), floored
    fl = np.clip(band, 1e-14, None)
    for i in range(1, 6):
        df[f"hr{i}{i + 1}"] = np.log10(fl[:, i + 1] / fl[:, i])
    df["log_epeak"] = df["log_epeak"].where(np.isfinite(df["log_epeak"]), 0.0)
    df["frac_var"] = df["frac_var"].fillna(0.0)
    df["assoc1"] = df["assoc1"].fillna("").replace("nan", "")
    return df


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Features with non-finite values (catalog infinities, missing fits) set to 0."""
    return df[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy()


def train_classifier(df: pd.DataFrame, seed=0):
    """Fit RF on associated pulsars vs AGN. Returns (model, cross-validated AUC)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score

    lab = df[df["cls"].isin(PSR_CLASSES | AGN_CLASSES)].copy()
    y = lab["cls"].isin(PSR_CLASSES).astype(int).to_numpy()
    X = feature_matrix(lab)
    if y.sum() < 50 or (1 - y).sum() < 50:
        raise RuntimeError("too few labelled sources to train")
    rf = RandomForestClassifier(n_estimators=500, min_samples_leaf=3,
                                class_weight="balanced", random_state=seed, n_jobs=-1)
    auc = cross_val_score(rf, X, y, cv=5, scoring="roc_auc").mean()
    rf.fit(X, y)
    return rf, float(auc)


def p_pulsar(model, df: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(feature_matrix(df))[:, 1]
