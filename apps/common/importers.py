from collections import defaultdict

from baseline.models import (
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    SourceOrganization,
)
from metadata.models import ReferenceData


class LivelihoodStrategyImporter:
    def strategy_type_lookup(self, val):
        # some complexity
        return val

    def save_from_bss_option_a_bit_more_hacky(self, instances):
        """
        Contains the business logic for extracting and saving a number of livelihood strategy objects from a BSS range.

        It assumes we just add a sprinkling of spreadsheet locations where needed, then do very bespoke code here
        making use of them.

        Returns list of objects saved to db.
        """
        lzb = instances[LivelihoodZoneBaseline]

        # We could do this in a very bespoke way for each and every model and field like so:
        map = {
            ref.name: ref
            for ref in lzb.spreadsheetreference_set.order_by("sequence").select_related("SpreadsheetPointOfInterest")
        }
        saved = []
        # Bespoke logic very specific to each model, eg, we hardcode that these are every other row on sheet Data, every row on Data2, etc
        i = 0
        ref = map["FirstLSStrategyType"]
        while ref.reference < map["LastLSStrategyType"]:
            ref = map["FirstLSStrategyType"].below(i)
            ls = LivelihoodStrategy(
                source_organizaton=instances[SourceOrganization],
                livelihood_zone=instances[LivelihoodZone],
            )
            ls.strategy_type = self.strategy_type_lookup(ref)
            i += 1
            saved.append(ls)
        return saved

    def save_from_bss_option_exhaustive_but_generic(self, instances):
        """
        Contains the business logic for extracting and saving a number of livelihood strategy objects.

        This approach assumes every field of every instance has a location (and optional regex) stored in
        SpreadsheetPointOfInterest. But the code is entirely generic.

        Whichever option we choose, we start by prepopulating these, and gradually automate their derivation.
        Roger's code can probably already prepopulate a significant portion of them.

        Returns list of objects saved to db.
        """
        lzb = instances[LivelihoodZoneBaseline]
        # Or we could do it generically - I like this idea although it is a lot of ref data (much identical between BSSes)
        map = defaultdict(lambda: defaultdict(lambda: defaultdict))
        for ref in lzb.spreadsheetreference_set.order_by("sequence", "instance_number").select_related(
            "SpreadsheetPointOfInterest"
        ):
            map[ref.spreadsheet_point_of_interest.model][ref.instance_number][
                ref.spreadsheet_point_of_interest.field
            ] = ref

        saved = []
        for model in map.keys():
            for instance_number in model.keys():
                instance = model()
                for field in instance_number.keys():
                    val = instance_number[field].get()
                    lookup_model = ReferenceData.get_model(model, field)
                    if lookup_model:
                        val = lookup_model.search(val, instance)
                    setattr(instance, field, val)
                instance.save()
                saved.append(instance)
        return saved
