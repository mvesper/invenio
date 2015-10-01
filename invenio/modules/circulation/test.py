from invenio.ext.template.context_processor import register_template_context_processor

@register_template_context_processor
def circulation_test():
    return 'yay'
