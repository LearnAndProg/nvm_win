# nvm_win
NodeJS Virtual Environment Management for Windows (Python 3)

A tiny and quick program coded during a rainy sunday ;) Made with Python 3.

This tools is inspired from nvm tool from Linux & Mac OS.
It helps a user to have many different nodejs environment in a signle machine and to allow to switch the active one.
Also it allows to have many environment with the same nodejs version but with different packages...

It owns a graphical user interface (double click on the exe) or also accepts command line parameters like :
on [envName]                 activate the env called envName 
off                          desactivate nodejs env manager 

Main packages used in this code:
* GUI : easygui
* HTML parser : lxml
* System calls: win32api
* Zip files management : zipfile
* Network calls : requests
* Locale management: gettext

All the code is in the main.py file.

Files & Directories : 
* img/        images used by the application - Do not modify
* locales/    traduction of french words (locale) - only French and English are available - Do not modify
* intall.bat  a batch script used by the programm. Do not use manually
* main.py     core code source (all in one....)
* bin/        contains a binary version of this tool... Unzip and enjoy...

Feel free to send me your remarks or evolutions/modifications
