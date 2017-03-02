from distutils.core import setup

from mp3_tagger import __version__


def read(path):
    return open(path).read()


setup(
    name='mp3-tagger',
    version=__version__,
    packages=['mp3_tagger'],
    url='https://github.com/artcom-net/mp3-tagger',
    license='MIT',
    author='Artem Kustov',
    author_email='artem.kustov@artcom-net.ru',
    description='ID3 data editor',
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Editors',
        'Topic :: Software Development :: Libraries'
    ]
)
