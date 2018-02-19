import json

from django.conf import settings
from django.template import Context, Template
from django.http import HttpResponse

from .helpers import get_translations


js_catalog_template = r"""
{% autoescape off %}
(function (globals) {

  var django = globals.django || (globals.django = {});

  /* gettext library */

  django.translations = {{ catalog_str }};

  django.localize = function (key, fallback, placeholders) {
    fallback = typeof(fallback) == "undefined" ? key : fallback;
    var value = django.translations[key];
    if (typeof(value) == 'undefined') {
      {% if not debug %}
      value = fallback;
      {% else %}
      value = '\{\{' + key + '\}\}';
      {% endif %}
    }
    if (placeholders && placeholders['plural']) {
      var plural = parseInt(placeholders['plural']);
      var values = value.split('|');
      delete placeholders['plural'];
      if (plural == 1 || values.length < 2) {
        value = value.split('|')[0];
      } else {
        value = value.split('|')[1];
      }
    }
    for (var ph in placeholders) {
      value = value.replace(':' + ph, placeholders[ph]);
    }
    return value;
  };

  /* formatting library */

  globals.localize = django.localize;

}(this));
{% endautoescape %}
"""


def render_javascript_catalog(translations=None):
    def _indent(s):
        return s.replace('\n', '\n  ')

    template = Template(js_catalog_template)
    context = Context({
        'catalog_str': _indent(json.dumps(
            translations, sort_keys=True, indent=2)) if translations else {},
        'debug': settings.LOCALIZE_DEBUG
    })

    return HttpResponse(template.render(context), 'text/javascript')


def javascript_catalog(request, domain='globaljs', packages=None):
    locale = request.LANGUAGE_CODE

    translations = get_translations(locale, domain)
    return render_javascript_catalog(translations)
