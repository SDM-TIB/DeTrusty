import os.path

from cssmin import cssmin
from rjsmin import jsmin


class Bundle(object):
    """A bundle is a unit to organize groups of media files, which filters to apply and where to store them.

    This class is inspired by the class ``Bundle`` from the ``webassets`` library.
    However, this class is only for the use within this project, and, hence, does not need to be general.
    This leads to the advantage that an instance of this class does not need an ``Environment`` class for
    translating relative paths to absolute ones. All paths are fixed for the use within this project.

    We are not relying on ``flask_assets`` and ``webassets`` as it seems that they are not actively
    maintained anymore. Additionally, those library do not work with Flask 3.0+.

    """

    STATIC_FOLDER = 'static/'

    def __init__(self, *contents, **options):
        self.contents = contents
        self.output = options.pop('output', None)
        self.filters = options.pop('filters', None)

        if self.output is not None:
            self.output = self.STATIC_FOLDER + self.output

    def build(self):
        """Builds the bundle.

        All files are combined and stored at the specified location.
        If any filters where given, they are applied before storing the combined bundle.

        Other than with the original implementation of this method, the output will always be generated;
        simulating a ``Bundle.build()`` call with ``force=True``.

        Step 1: Read all input files into one string
        Step 2: Apply filters
        Step 3: Write output file

        """
        if self.contents is None or self.output is None:
            return

        content = ''
        for file in self.contents:
            if not os.path.isfile(file):
                continue

            content += open(file, 'r').read()
            if not content.endswith('\n'):
                content += '\n'

        if self.filters == 'cssmin':
            content = cssmin(content)
        elif self.filters == 'rjsmin':
            content = jsmin(content, keep_bang_comments=False)
        else:
            raise NotImplementedError('Filter ' + self.filters + ' not implemented.')

        out_dir = os.path.dirname(self.output)
        os.makedirs(out_dir, exist_ok=True)
        open(self.output, 'w').write(content)


NPM_PATH = 'node_modules/'
JS_PATH = 'js/'
CSS_PATH = 'css/'

bundles = {
    'yasgui_js': Bundle(
        NPM_PATH + '@zazuko/yasgui/build/yasgui.min.js',
        filters='rjsmin',
        output=JS_PATH + 'yasgui.min.js'
    ),
    'yasgui_css': Bundle(
        NPM_PATH + '@zazuko/yasgui/build/yasgui.min.css',
        filters='cssmin',
        output=CSS_PATH + 'yasgui.min.css'
    ),
    'd3_js': Bundle(
        NPM_PATH + 'd3/dist/d3.min.js',
        filters='rjsmin',
        output=JS_PATH + 'd3.min.js'
    )
}

for name, bundle in bundles.items():
    print('    building bundle:', name)
    bundle.build()
