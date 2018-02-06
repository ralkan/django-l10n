from django.utils.translation import get_language

from .helpers import translate_by_key


def localize(key, default=None, **kwargs):
    lang_code = get_language()
    return translate_by_key(lang_code, key, default, **kwargs)
