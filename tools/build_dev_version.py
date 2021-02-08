import datetime
import os
import re

proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

version = datetime.datetime.now().strftime('.dev%y%m%d%H%M')
version_path = os.path.join(proj_dir, 'pywebio', '__version__.py')

content = open(version_path).read()
new_content = re.sub(r'__version__ = "(.*)?"', r'__version__ = "\g<1>%s"' % version, content)
new_content += '\n__commit_hash__ = %r' % os.environ.get('GITHUB_SHA', '')[:8]
open(version_path, 'w').write(new_content)

about = {}
exec(new_content, about)
print(about['__version__'])
