from common.lookups import Lookup

from .models import Community


class CommunityLookup(Lookup):
    model = Community
    id_fields = ["id"]
    parent_fields = ["livelihood_zone_baseline"]
    lookup_fields = (
        "code",
        "name",
        "full_name",
    )
