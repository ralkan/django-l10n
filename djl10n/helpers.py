import os
import toml

from collections import defaultdict

from django.conf import settings


_localize_translations = defaultdict(dict)
_localize_filemtimes = defaultdict(dict)
_localize_file_paths = defaultdict(dict)


def parse_translations_file(lang_path):
    file_path = os.path.abspath(lang_path)

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            translations = toml.loads(f.read())
    else:
        translations = {}
    return translations


def get_translations(lang_code, domain='global', fallback=True):
    global _localize_translations
    global _localize_filemtimes
    global _localize_file_paths

    if domain not in _localize_file_paths[lang_code]:
        filename = '{}.toml'.format(domain)
        lang_path = os.path.join(settings.LOCALE_PATHS[0], lang_code, filename)
        # Fallback to default file (ie. for English)
        if fallback and not os.path.exists(lang_path):
            lang_path = os.path.join(
                settings.LOCALE_PATHS[0], 'default', filename)
        _localize_file_paths[lang_code][domain] = lang_path
    else:
        lang_path = _localize_file_paths[lang_code][domain]

    lang_translations = _localize_translations[lang_code]
    lang_filemtime = _localize_filemtimes[lang_code]

    translations = lang_translations.get(domain)

    if not translations:
        translations = parse_translations_file(lang_path)
        lang_translations[domain] = translations
        try:
            lang_filemtime[domain] = os.path.getmtime(
                os.path.abspath(lang_path))
        except OSError:
            pass
    else:
        _filemtime = lang_filemtime.get(domain)
        if os.path.getmtime(os.path.abspath(lang_path)) > _filemtime:
            translations = parse_translations_file(lang_path)
            lang_translations[domain] = translations
            try:
                lang_filemtime[domain] = os.path.getmtime(
                    os.path.abspath(lang_path))
            except OSError:
                pass

    return translations


def save_translations(lang_code, translations, domain='global'):
    filename = '{}.toml'.format(domain)
    locale_path = os.path.join(settings.LOCALE_PATHS[0], lang_code)

    if not os.path.isdir(os.path.abspath(locale_path)):
        os.makedirs(locale_path)

    file_path = os.path.abspath(os.path.join(locale_path, filename))
    with open(file_path, 'w') as f:
        toml.dump(translations, f)


def translate_by_key(lang_code, key, default=None, **kwargs):
    translations = get_translations(lang_code)

    # Just return the key if no default is specified
    if settings.LOCALIZE_DEBUG:
        default = "{{%s}}" % key
    sent = translations.get(key.lower(), default or key)
    plural = kwargs.pop('plural', None)
    if plural is not None:
        sents = sent.split('|')
        if len(sents) > 1:
            if plural == 1:
                sent = sents[0]
            else:
                sent = sents[1]

    for k in kwargs:
        sent = sent.replace(':%s' % k, unicode(kwargs[k]))

    if key.isupper():
        sent = sent.upper()
    elif key.istitle():
        sent = sent.title()
    elif key[:1].isupper():
        sent = sent[:1].upper() + sent[1:]
    return unicode(sent)
