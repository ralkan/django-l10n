from django.utils.translation import get_language
from django.utils.functional import lazy
from django.utils import six

from .helpers import translate_by_key


def localize(key, default=None, **kwargs):
    lang_code = get_language()
    return translate_by_key(lang_code, key, default, **kwargs)


localize_lazy = lazy(localize, six.text_type)
