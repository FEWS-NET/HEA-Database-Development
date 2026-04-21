from pathlib import Path

from django.db import migrations

reverse_sql = """
DROP FUNCTION IF EXISTS get_annual_kcals_cost (
	p_baseline_id BIGINT,
	p_wealth_group_category_code character varying(60)
);
"""

sql = Path(__file__).with_suffix(".sql").read_text()


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0032_percentages_as_float_fields"),
    ]

    operations = [
        migrations.RunSQL(sql=sql, reverse_sql=reverse_sql),
    ]
