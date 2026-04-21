CREATE OR REPLACE FUNCTION get_annual_kcals_cost (
	p_baseline_id BIGINT,
	p_wealth_group_category_code character varying(60)
) RETURNS numeric LANGUAGE PLPGSQL STABLE PARALLEL SAFE AS $$
DECLARE
    v_main_staple_count integer;
    v_household_size numeric;
    v_kcals_per_unit numeric;
    v_price numeric;
    v_total_percentage_kcals numeric := 0;
    v_total_expenditure numeric := 0;
BEGIN
	/*
	Calculate the annual cost of 100% of recommended kcals for a person in a Wealth Group.

	This is required to calculate the combined food and income.

	It is defined as the cost of providing 100% of required kcals for the
	Wealth Group divided by the average_household_size. The cost is
	calculated as the cost of Basket 2 (Other food survival) plus the cost
	of providing the remainder of kcals by purchasing the main staple. All
	costs are in the currency for the BSS.

	This calculation is based on the formulae in the Graphs worksheet.
	*/
    -- Count POOR main staple rows
    SELECT COUNT(*)
      INTO v_main_staple_count
      FROM baseline_livelihoodproductcategory lpc
      JOIN baseline_livelihoodactivity lay
        ON lpc.baseline_livelihood_activity_id = lay.id
      JOIN baseline_wealthgroup wgp
        ON lay.wealth_group_id = wgp.id
     WHERE lpc.basket = 1
       AND wgp.livelihood_zone_baseline_id = p_baseline_id
       AND wgp.wealth_group_category_code = p_wealth_group_category_code;

    IF v_main_staple_count = 0 THEN
        RETURN NULL;
    ELSIF v_main_staple_count > 1 THEN
        RAISE EXCEPTION
            'Livelihood Zone Baseline % contains more than one Main Staple for Wealth Group %s',
            p_baseline_id, p_wealth_group_category_code;
    END IF;

    -- Fetch the single main staple row for the Wealth Group
    SELECT
        wgp.average_household_size,
        COALESCE(
            NULLIF(lay.extra ->> 'product__kcals_per_unit', '')::numeric,
            cpt.kcals_per_unit::numeric
        ),
        lay.price::numeric
      INTO
        v_household_size,
        v_kcals_per_unit,
        v_price
      FROM baseline_livelihoodproductcategory lpc
      JOIN baseline_livelihoodactivity lay
        ON lpc.baseline_livelihood_activity_id = lay.id
      JOIN baseline_wealthgroup wgp
        ON lay.wealth_group_id = wgp.id
      JOIN baseline_livelihoodstrategy lsy
        ON lay.livelihood_strategy_id = lsy.id
      JOIN common_classifiedproduct cpt
        ON lsy.product_code = cpt.cpc
     WHERE lpc.basket = 1
       AND wgp.livelihood_zone_baseline_id = p_baseline_id
       AND wgp.wealth_group_category_code = p_wealth_group_category_code
     LIMIT 1;

    -- Aggregate other-food survival basket for the Wealth Group
    SELECT
        COALESCE(SUM(lay.percentage_kcals * lpc.percentage_allocation_to_basket), 0)::numeric,
        COALESCE(SUM(lay.expenditure * lpc.percentage_allocation_to_basket), 0)::numeric
      INTO
        v_total_percentage_kcals,
        v_total_expenditure
      FROM baseline_livelihoodproductcategory lpc
      JOIN baseline_livelihoodactivity lay
        ON lpc.baseline_livelihood_activity_id = lay.id
      JOIN baseline_wealthgroup wgp
        ON lay.wealth_group_id = wgp.id
     WHERE lpc.basket = 2
       AND wgp.livelihood_zone_baseline_id = p_baseline_id
       AND wgp.wealth_group_category_code = p_wealth_group_category_code;

    RETURN (
        (
            2100::numeric
            * 365
            * v_household_size
            * (1 - v_total_percentage_kcals)
            / v_kcals_per_unit
            * v_price
        )
        + v_total_expenditure
    ) / v_household_size;
END;
$$;

REVOKE ALL ON FUNCTION get_annual_kcals_cost (
	p_baseline_id BIGINT,
	p_wealth_group_category_code character varying(60)
) 
FROM
	PUBLIC;