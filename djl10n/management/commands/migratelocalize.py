import os
import sys
import toml
import re

from optparse import make_option
from unidecode import unidecode

from django.core.management import BaseCommand


REGEX_PATTERNS = {
    'html': {
        'matcher': r'{% ?(trans[ ]+[\'"]([^{}<>]*?)[\'"]) ?%}',
        'sub': r'trans[ ]+[\'"](.*?)[\'"]',
        'replace': 'localize \'{}\' \'{}\''
    },
    'js': {
        'matcher': r'[{ ,(](gettext\([\'"]([^{}<>]*?)[\'"]\))',
        'sub': r'gettext\([\'"](.*?)[\'"]\)',
        'replace': 'localize(\'{}\', \'{}\')'
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
        global REGEX_PATTERNS
        ext = os.path.splitext(path)[1]
        if ext == '.js':
            self._search_and_replace(path, maxlen, verbose,
                                     patterns=REGEX_PATTERNS['js'])
        if ext == '.html':
            self._search_and_replace(path, maxlen, verbose,
                                     patterns=REGEX_PATTERNS['html'])

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
                                key, val.replace("'", "\\'")), actual)
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
