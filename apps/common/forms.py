from treebeard.forms import MoveNodeForm, movenodeform_factory
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ClassifiedProduct


class MoveCharNodeForm(MoveNodeForm):
    """
    Form to handle moving a node in an MP tree with a CharField primary key

    The tree doesn't have an integer primary key, so override the TypedChoiceField
    """

    _ref_node_id = forms.ChoiceField(required=False, label=_("Relative to"))


ClassifiedProductForm = movenodeform_factory(ClassifiedProduct, form=MoveCharNodeForm)
