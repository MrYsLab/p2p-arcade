from setuptools import setup

with open('pypi_desc.md') as f:
    long_description = f.read()

setup(
    name='p2p_arcade',
    version='0.1',
    packages=[
        'p2p_arcade',
    ],
    install_requires=[
        'python_banyan', 'arcade', 'msgpack', 'zmq', 'psutil'
    ],

    entry_points={
        'console_scripts': [
            'p2pa = p2p_arcade.p2p_arcade:p2p_arcade',
        ]
    },

    url='https://github.com/MrYsLab/p2p-arcade',
    license='GNU Affero General Public License v3 or later (AGPLv3+)',
    author='Alan Yorinks',
    author_email='MisterYsLab@gmail.com',
    description='A Non-Blocking Event Driven Applications Framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['arcade',  'p2p', 'games', 'arcade',],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Topic :: Education',

    ],
)
