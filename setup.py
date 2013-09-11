import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '0.10.5'

setup(name='Products.PloneGetPaid',
      version=version,
      description="E-commerce framework for Plone",
      long_description=(
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Download\n'
        '**********************\n'
        ),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Framework :: Zope3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries",
      ],
      keywords='commerce donation zope plone getpaid',
      author='GetPaid Team',
      author_email='getpaid-dev@googlegroups.com',
      url='http://www.plonegetpaid.com/',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.app.intid',
          'getpaid.core>=0.9.0',
          'getpaid.hurry.workflow',
          'getpaid.nullpayment>=0.5.0',
          'getpaid.wizard',
          'getpaid.ore.viewlet',
          'getpaid.yoma.batching',
          'zc.table',
          'zope.interface',
          'zope.component',
          # -*- Extra requirements: -*-
      ],
      extras_require={
          # we should be able to get rid of this
          'test':  ['zope.app.testing'],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
""",
      )
