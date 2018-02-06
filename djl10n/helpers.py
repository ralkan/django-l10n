import os
import toml

from collections import defaultdict

from django.conf import settings


_localize_translations = defaultdict(dict)
_localize_filemtimes = defaultdict(dict)


def get_translations(lang_code, domain='global'):
    global _localize_translations
    filename = '{}.toml'.format(domain)

    lang_translations = _localize_translations[lang_code]
    translations = lang_translations.get(domain)
    if not translations:
        lang_path = os.path.join(settings.LOCALE_PATHS[0], lang_code, filename)

        # Fallback to default file (ie. for English)
        if not os.path.exists(lang_path):
            lang_path = os.path.join(
                settings.LOCALE_PATHS[0], 'default', filename)

        file_path = os.path.abspath(lang_path)

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                translations = toml.loads(f.read())
        else:
            translations = {}

        lang_translations[domain] = translations

    return translations


def translate_by_key(lang_code, key, default=None, **kwargs):
    translations = get_translations(lang_code)

    # Just return the key if no default is specified
    if settings.LOCALIZE_DEBUG:
        default = "{{%s}}" % key
    sent = translations.get(key, default or key)
    plural = kwargs.get('plural')
    if plural is not None:
        del kwargs['plural']
        sents = sent.split('|')
        if plural == 1:
            sent = sents[0]
        else:
            sent = sents[1]

    for k in kwargs:
        sent = sent.replace(':%s' % k, kwargs[k])
    return sent
