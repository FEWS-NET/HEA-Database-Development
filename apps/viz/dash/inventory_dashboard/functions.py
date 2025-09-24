import pandas as pd

from baseline.models import (
    LivelihoodActivity,
    LivelihoodZoneBaseline,
    LivelihoodZoneBaselineCorrection,
    WealthGroupCharacteristicValue,
)


def get_livelihood_zone_baseline():
    qs = LivelihoodZoneBaseline.objects.select_related(
        "livelihood_zone__country",
        "source_organization",
    ).values_list(
        "id",
        "livelihood_zone__country__name",
        "livelihood_zone__name_en",
        "source_organization__name",
        "livelihood_zone__code",
        "main_livelihood_category__name_en",
    )
    columns = [
        "id",
        "country",
        "livelihood_zone",
        "source_organization",
        "zone_code",
        "main_livelihood_category",
    ]
    df = pd.DataFrame(list(qs), columns=columns)

    return df


def get_livelihood_activity_dataframe():
    queryset = LivelihoodActivity.objects.select_related(
        "livelihood_strategy",
        "livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    ).values(
        "id",
        "livelihood_zone_baseline__livelihood_zone__country__name",
        "livelihood_strategy__strategy_type",
        "wealth_group",
        "wealth_group__community",
    )

    df = pd.DataFrame(list(queryset))

    df = df.rename(
        columns={
            "id": "activity_id",
            "livelihood_zone_baseline__livelihood_zone__country__name": "country",
            "livelihood_strategy__strategy_type": "strategy_type",
            "wealth_group": "wealth_group_id",
            "wealth_group__community": "community_id",
        }
    )
    if df.empty:
        return df
    # Add baseline/community flag
    df["data_level"] = df["community_id"].apply(lambda x: "baseline" if pd.isna(x) else "community")

    return df


def get_bss_corrections():
    queryset = LivelihoodZoneBaselineCorrection.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
    )

    data = []
    for correction in queryset:
        data.append(
            {
                "id": correction.id,
                "country": correction.livelihood_zone_baseline.livelihood_zone.country.name,
                "bss": str(correction.livelihood_zone_baseline),
            }
        )

    df = pd.DataFrame(data)
    return df


def get_wealthcharactestics():
    queryset = (
        WealthGroupCharacteristicValue.objects.select_related(
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country", "wealth_characteristic"
        )
        .exclude(value__isnull=True)
        .exclude(value__exact="")
    )

    data = []
    for wc in queryset:
        wealth_characteristic = str(wc.wealth_characteristic)
        if wc.wealth_characteristic.has_product:
            wealth_characteristic += f":{wc.product}"

        data.append(
            {
                "id": wc.id,
                "country": wc.wealth_group.livelihood_zone_baseline.livelihood_zone.country.name,
                "bss": str(wc.wealth_group.livelihood_zone_baseline),
                "wealth_characteristic": wealth_characteristic,
                "value": wc.value,
            }
        )

    df = pd.DataFrame(data)
    return df
