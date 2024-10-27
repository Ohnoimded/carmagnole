
from django import template
from mjml import mjml2html

register = template.Library()


class MjmlRenderer(template.Node):
    def __init__(self, node_list):
        self.node_list = node_list

    def render(self, context):
        tags = self.node_list.render(context)
        return mjml2html(tags)


@register.tag
def mjml(parser, token):
    node_list = parser.parse(("endmjml",))
    parser.delete_first_token()
    return MjmlRenderer(node_list)