import os.path

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

    
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='proxifier',
      version="0.1",
      author="Mike Spindel",
      author_email="deactivated@gmail.com",
      license="MIT",
      keywords="http proxy mitm wsgi",
      url="http://github.com/deactivated/proxifier",
      description='Easy application-specific proxies.',
      packages=find_packages(exclude=['ez_setup']),
      long_description=read('README.rst'),
      zip_safe=False,
      classifiers=[
          "Development Status :: 4 - Beta",
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Programming Language :: Python"],
      install_requires=[
        'webob'
        ])
