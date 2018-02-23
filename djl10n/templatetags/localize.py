import re

from django import template
from django.utils.translation import get_language

from ..helpers import translate_by_key


register = template.Library()


@register.simple_tag(takes_context=True)
def localize(context, key, default=None, **kwargs):
    tmp_kwargs = {}
    for k, v in kwargs.iteritems():
        tmp_v = v
        matches = []
        if k != 'plural':
            matches = re.findall(r'({{[ ]*([\w\.]+)[ ]*}})', unicode(tmp_v))
        for m in matches:
            if '.' in m[1]:
                _parts = m[1].split('.')
                value = context.get(_parts.pop(0))
                if value:
                    for part in _parts:
                        if any((type(value) is dict, type(value) is list)):
                            value = value[part]
                        else:
                            value = getattr(value, part)
            else:
                value = context.get(m[1])
            if value:
                tmp_v = re.sub(m[0], value, tmp_v)
        tmp_kwargs[k] = tmp_v
    lang_code = get_language()
    return translate_by_key(lang_code, key, default, **tmp_kwargs)
