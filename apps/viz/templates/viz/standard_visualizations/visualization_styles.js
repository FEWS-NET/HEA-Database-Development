{% load is_number is_list %}
window.standardVizStyles = {{% for variable, value in style_variables.items %}
    {{ variable }}: {% if value|is_number %}{{ value }}{% elif value|is_list %}[{% for element in value %}"{{ element }}"{% if not forloop.last %}, {% endif %}{% endfor %}]{% else %}"{{ value }}"{% endif %}{% if not forloop.last %},{% endif %}{% endfor %}
}