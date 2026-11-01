"""Whether the a2uicatalog Python package is on PyPI yet. The site generators read this so no page links a
package that does not exist. Flip PYPI_PUBLISHED to True in the commit that follows the first release
(tag py-v0.1.0), then run gen_trust_pages.py and gen_openapi.py."""
PYPI_PUBLISHED = True
PYPI_URL = "https://pypi.org/project/a2uicatalog/"
