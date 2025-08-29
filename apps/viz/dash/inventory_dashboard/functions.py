import pandas as pd
import requests

# API Endpoints
LIVELIHOOD_STRATEGY_URL = "https://headev.fews.net/api/livelihoodstrategy/"
WEALTH_GROUP_URL = "https://headev.fews.net/api/wealthgroupcharacteristicvalue/"
LIVELIHOOD_ACTIVITY_URL = "https://headev.fews.net/api/livelihoodactivity/"


def fetch_data(api_url):
    """
    Fetch data from the given API endpoint and return as a Pandas DataFrame.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


def prepare_livelihood_data(df):
    """
    Prepare livelihood strategy data for visualization.
    """
    df.rename(columns={"livelihood_zone_country": "country_code"}, inplace=True)
    df["ls_baseline_date"] = df["livelihood_zone_baseline_label"].str.split(": ").str[1]
    df["ls_baseline_month"] = pd.to_datetime(df["ls_baseline_date"], errors="coerce").dt.month
    return df


def prepare_wealth_group_data(df):
    """
    Prepare wealth group data for visualization.
    """
    df.rename(columns={"livelihood_zone_country_code": "country_code"}, inplace=True)

    if "livelihood_zone_baseline_label" in df.columns:
        df["ls_baseline_date"] = df["livelihood_zone_baseline_label"].str.split(": ").str[1]
    else:
        df["ls_baseline_date"] = None

    df["ls_baseline_month"] = pd.to_datetime(df["ls_baseline_date"], errors="coerce").dt.month

    month_mapping = {month: pd.Timestamp(f"2023-{month:02}-01").strftime("%B") for month in range(1, 13)}

    if "created_date" in df.columns:
        df["created_month"] = pd.to_datetime(df["created_date"], errors="coerce").dt.month.map(month_mapping)
    else:
        df["created_month"] = pd.to_datetime(df["ls_baseline_date"], errors="coerce").dt.month.map(month_mapping)

    if "community_name" in df.columns:
        df["Record Type"] = df["community_name"].apply(lambda x: "Summary Data" if pd.isna(x) else "Community Data")
    else:
        df["Record Type"] = "Community Data"

    return df


# Fetch and prepare data
livelihood_data = fetch_data(LIVELIHOOD_STRATEGY_URL)
wealth_group_data = fetch_data(WEALTH_GROUP_URL)

clean_livelihood_data = prepare_livelihood_data(livelihood_data)
clean_wealth_group_data = prepare_wealth_group_data(wealth_group_data)
