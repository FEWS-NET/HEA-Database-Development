import re

from baseline.models import LivelihoodStrategy
from common.models import ClassifiedProduct


def format_readable_string(s):
    readable_str = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return readable_str.capitalize()


def build_filter_tree():
    results = []
    # Get distinct and sorted strategy types
    strategy_types = sorted(LivelihoodStrategy.objects.values_list("strategy_type", flat=True).distinct())

    for strategy_type in strategy_types:
        result = {"value": strategy_type, "title": format_readable_string(strategy_type), "children": []}

        # Get distinct products for each strategy type
        products = (
            LivelihoodStrategy.objects.filter(strategy_type=strategy_type).values_list("product", flat=True).distinct()
        )

        for product_cpc in products:
            product = ClassifiedProduct.objects.get(cpc=product_cpc)
            result["children"] = get_product_hierarchy(product, current_tree=result["children"])

        results.append(result)
    return results


def get_product_hierarchy(product, current_tree=None):
    """
    Builds the product hierarchy from the root to the current product.
    """
    hierarchy_nodes = []
    current_node = product

    # Traverse all the way up to the root and collect nodes
    while current_node is not None:
        hierarchy_nodes.append(current_node)
        current_node = current_node.get_parent()

    # Reverse the list to start building from the root downwards
    hierarchy_nodes.reverse()

    # Initialize current_tree as a list of children if not provided
    if current_tree is None:
        current_tree = []

    current_parent = {"children": current_tree}  # A temporary root node to hold the tree

    # To make sure the nodes don't appear again with in the branch of the tree within the strategy type
    for node in hierarchy_nodes:
        existing_node = next((child for child in current_parent["children"] if child["value"] == node.cpc), None)

        if existing_node:
            # If the node exists, move down into this node for further nesting
            current_parent = existing_node
        else:
            # If the node doesn't exist, create a new node
            new_node = {"value": node.cpc, "title": node.description, "children": []}
            current_parent["children"].append(new_node)
            current_parent = new_node

    # Return the children (which is a list of nodes) at the topmost level
    return current_tree
