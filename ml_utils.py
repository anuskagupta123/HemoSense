# ml_utils.py
import numpy as np

TIP_MAP = {
    "Normal": [
        "Maintain a balanced diet rich in iron, vitamin B12 and folate.",
        "Keep doing routine health check-ups.",
        "Stay hydrated and active."
    ],
    "Anemia": [
        "Increase iron-rich foods such as leafy greens, red meat, and pulses.",
        "Avoid tea and coffee immediately after meals to help iron absorption.",
        "Consult a doctor for further evaluation and supplements if needed."
    ],
    "Unknown": [
        "Please consult a healthcare provider for proper evaluation."
    ]
}

def prepare_features(age, gender, hb, mch, mchc, mcv):
    """
    Prepare feature array according to model expectations.
    Adjust mapping if your model expects different encoding.
    Current mapping: gender: female->0, male->1, other->2
    Feature order: [gender_val, hb, mch, mchc, mcv]
    """
    g = (gender or "").lower()
    gender_map = {"female": 0, "male": 1, "other": 2}
    gender_val = gender_map.get(g, 2)

    mch_val = float(mch) if mch not in (None, "", "None") else 0.0
    mchc_val = float(mchc) if mchc not in (None, "", "None") else 0.0
    mcv_val = float(mcv) if mcv not in (None, "", "None") else 0.0

    return np.array([[gender_val, float(hb), mch_val, mchc_val, mcv_val]])

def get_tips(category):
    return TIP_MAP.get(category, TIP_MAP["Unknown"])
