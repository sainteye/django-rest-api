from setuptools import setup, find_packages

import rest_api as distmeta


CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet',
    'Topic :: API',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Operating System :: OS Independent',
]


setup(
    name='django-rest-api',
    version='.'.join(map(str, distmeta.__version__)),
    author=distmeta.__author__,
    author_email=distmeta.__contact__,
    url=distmeta.__homepage__,
    license='2-clause BSD',
    description="Rest api framework for Django",
    install_requires=[],
    packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
    include_package_data=True,
    classifiers=CLASSIFIERS,
    test_suite='tests',
)
