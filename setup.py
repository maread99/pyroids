#! /usr/bin/env python

"""Setup file for pyroids package."""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()

setup(name='pyroids',
      version='0.9.0',
      url='https://github.com/maread99/pyroids',
      author='Marcus Read',
      author_email='marcusaread@gmail.com',
      description='Asteroids game',
      long_description=long_description,
      long_description_content_type='text/markdown',
      license='MIT',
      classifiers=['License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Topic :: Games/Entertainment :: Arcade'
                   ],
      keywords='asteroids arcade game pyglet multiplayer',
      project_urls={'Source': 'https://github.com/maread99/pyroids',
                    'Tracker': 'https://github.com/maread99/pyroids/issues',
                    },
      packages=find_packages(),
      install_requires=['pyglet>=1.4'],
      python_requires='~=3.6',
      package_data={'pyroids': ['resources/*.png',
                                'resources/*.wav', 
                                'config/*.py'
                                ],
                    },
      entry_points={'console_scripts': ['pyroids=pyroids:launch']}
      )