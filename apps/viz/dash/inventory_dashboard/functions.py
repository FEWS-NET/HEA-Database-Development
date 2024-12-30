import pandas as pd
import requests


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
    df["ls_baseline_month"] = pd.to_datetime(df["ls_baseline_date"], errors="coerce").dt.month_name()
    return df


def prepare_wealth_group_data(df):
    """
    Prepare wealth group data for visualization.
    """
    df.rename(columns={"livelihood_zone_country_code": "country_code"}, inplace=True)
    return df
