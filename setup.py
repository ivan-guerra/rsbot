from setuptools import setup, find_packages

setup(
    name='rsbot',
    version='1.0',
    packages=find_packages(),
    install_requires=['pyautogui', 'pynput'],
    entry_points={
        'console_scripts': [
            'rsbot = rsbot.bot:main',
        ],
    },
)
