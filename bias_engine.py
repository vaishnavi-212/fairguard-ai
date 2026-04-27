import pandas as pd

def detect_bias(df):

    male_selected = len(
        df[(df["gender"]=="Male") & (df["selected"]==1)]
    )

    female_selected = len(
        df[(df["gender"]=="Female") & (df["selected"]==1)]
    )

    if male_selected > female_selected:
        risk="Medium Bias Risk"
        score=72
    else:
        risk="Low Bias Risk"
        score=90

    return {
        "Fairness Score":score,
        "Risk":risk,
        "Issue":"Possible gender disparity detected"
    }