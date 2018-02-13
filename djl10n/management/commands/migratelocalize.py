import os
import sys
import toml
import re

from optparse import make_option
from unidecode import unidecode

from django.core.management import BaseCommand


PATTERNS = {
    'html': {
        'matcher': r'{% ?(trans[ ]+[\'"]([^{}<>]*?)[\'"]) ?%}',
        'sub': r'^trans[ ]+[\'"](.*?)[\'"]$',
        'replace': 'localize "{}" "{}"',
        'process_val': lambda val: val.replace('"', '\\"')
    },
    'js': {
        'matcher': r'[{ ,(](gettext\([\'"]([^{}<>]*?)[\'"]\))',
        'sub': r'gettext\([\'"](.*?)[\'"]\)',
        'replace': 'localize(\'{}\', \'{}\')',
        'process_val': lambda val: val.replace("'", "\\'")
    },
}


class Command(BaseCommand):
    translations = {}
    inv_translations = {}

    option_list = BaseCommand.option_list + (
        make_option('-t', '--transfile', dest='transfile',
                    help="Path to translation file"),
        make_option('-f', '--file', dest='file',
                    help='Path to the file to replace', default=None),
        make_option('-d', '--directory', dest='directory',
                    help='Directory to search in', default=None),
        make_option('-e', '--extension', dest='extension', default='js',
                    help='File Extension (eg. js, py)'),
        make_option('-m', '--maxlen', dest='maxlen', default=70,
                    help='Max length of characters for the string to replace'),
    )

    def search_and_replace(self, path, maxlen, verbose=False):
        global PATTERNS
        ext = os.path.splitext(path)[1]
        if ext == '.js':
            has_translation = self._search_and_replace(
                path, maxlen, verbose, patterns=PATTERNS['js'])
        if ext == '.html':
            has_translation = self._search_and_replace(
                path, maxlen, verbose, patterns=PATTERNS['html'])
            if has_translation:
                self._load_localize_template_tag(path)

    def _load_localize_template_tag(self, path):
        re_tt_extends = re.compile(r'{% extends [\'"](.*)[\'"] %}')
        add_tag = False
        with open(path, 'r') as f:
            contents = f.read()
            templatetags = re.findall(r'{% load (\w+) %}', contents)
            if 'localize' not in templatetags:
                with open('{}.new'.format(path), 'w') as fnew:
                    has_extends = False
                    if re_tt_extends.search(contents):
                        has_extends = True

                    lines = contents.splitlines()
                    linecount = len(lines)
                    new_lines = []

                    for ind in xrange(linecount):
                        line = lines[ind]
                        if not add_tag:
                            if has_extends:
                                if (line != '' and
                                        not re_tt_extends.search(line)):
                                    new_lines.append('{% load localize %}')
                                    add_tag = True
                            else:
                                new_lines.append('{% load localize %}')
                                add_tag = True
                        new_lines.append(line)
                    new_contents = '\n'.join(new_lines)
                    fnew.write(new_contents)
        if add_tag:
            os.remove(path)
            os.rename('{}.new'.format(path), path)

    def _search_and_replace(self, path, maxlen, verbose, patterns):
        has_translation = False
        with open(path, 'r') as f, open('{}.new'.format(path), 'w') as fnew:
            m = re.compile(patterns['matcher'])
            for line in f.readlines():
                matches = m.findall(line)
                if len(matches) > 0:
                    has_translation = True
                    replaced_line = line
                    for match in matches:
                        actual = match[0]
                        val = match[1]
                        if len(val) > maxlen:
                            continue

                        if val in self.inv_translations:
                            key = self.inv_translations[val]
                        else:
                            key = re.sub('[^A-Za-z0-9 +/&%]+', '', val)
                            if isinstance(key, unicode):
                                key = unidecode(key)
                            key = re.sub('_+', '_', key.lower().replace(
                                ' ', '_').replace('/', '_')
                                         .replace('&', '_')
                                         .replace('%', '_percent_')
                                         .replace('+', '_plus_')).strip('_')
                            if key not in self.translations:
                                self.translations[key] = val

                        replaced = re.sub(
                            patterns['sub'],
                            patterns['replace'].format(
                                key, patterns['process_val'](val)), actual)
                        replaced_line = replaced_line.replace(actual, replaced)
                    if verbose and line != replaced_line:
                        sys.stdout.write(line.replace('\n', '').strip() + '\n')
                        sys.stdout.write(replaced_line.strip() + '\n\n')
                    fnew.write(replaced_line)
                else:
                    fnew.write(line)
        if not has_translation:
            os.remove('{}.new'.format(path))
        else:
            os.remove(path)
            os.rename('{}.new'.format(path), path)
        return has_translation

    def handle(self, *args, **options):
        transfile_path = options['transfile']
        if not transfile_path:
            sys.exit('Option --transfile is required')

        maxlen = options['maxlen']
        verbose = True if options['verbosity'] == '1' else False

        if os.path.exists(transfile_path):
            with open(transfile_path, 'r') as tf:
                self.translations = toml.loads(tf.read())

        self.inv_translations = {
            v: k for k, v in self.translations.iteritems()}

        if options['file']:
            file_path = os.path.abspath(options['file'])
            if not os.path.isfile(file_path):
                sys.exit('{} is not a file or the file does not exist.'.format(
                    args.file))
            self.search_and_replace(file_path, maxlen, verbose)
        else:
            extension = '.{}'.format(options['extension'])
            for directory, _, filenames in os.walk(options['directory']):
                for filename in filenames:
                    if os.path.splitext(filename)[1] == extension:
                        file_path = os.path.join(directory, filename)
                        self.search_and_replace(file_path, maxlen, verbose)

        with open(transfile_path, 'w') as tf:
            toml.dump(self.translations, tf)
