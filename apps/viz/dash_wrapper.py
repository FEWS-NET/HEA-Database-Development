from django_plotly_dash import DjangoDash


class SecureDjangoDash(DjangoDash):
    """
    An extended version of DjangoDash that allows fine-grained control of permissions
    and clickjacking protection
    """

    xframe_options = "DENY"  # None (i.e. Allow) or SAMEORIGIN or DENY
    login_required = True
    permission_required = None

    def __init__(self, *args, **kwargs):
        self.permission_required = kwargs.pop("permission_required", None)
        super().__init__(*args, **kwargs)
