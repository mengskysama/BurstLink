BurstLink
===========

A fake multiple connection proxy based on Twisted

### NOTE

1. This is a beta version and may have bugs
2. Currently **NOT** support encrypt transfer 

## Installation

### Client

#### Windows

1. Install [python 2.7](https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi)
2. Install [Twisted](https://pypi.python.org/packages/2.7/T/Twisted/Twisted-14.0.2.win32-py2.7.msi) and [zope](https://pypi.python.org/packages/2.7/z/zope.interface/zope.interface-4.1.1.win32-py2.7.exe#md5=8b36e1fcd506ac9fb325ddf1c7238b07)
3. Download from [this](https://github.com/mengskysama/BurstLink/archive/master.zip)

Note: suggest install [iocp support](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py2.7.exe/download)

#### Linux

Same as server
    
### Server

#### Debian/Ubuntu: 

    # apt-get install python-pip
    # pip install twisted

#### CentOS:

    # yum install python-setuptools
    # easy_install pip
    # pip install twisted
    
## Configuration

Edit `config.py`

## Usage

Server:

    python server.py

Client:

    python local.py
    
Or (for windows double click it)

If your system use Python3 by default(eg: Arch Linux)

    python2 local.py
    
# License

GPLv3

#敢不敢不把翻转传输给墙了，人在做天在看
