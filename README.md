BurstLink
===========

A fake multi connection proxy based on Twisted

### NOTE

1. This a beta version and may have bugs
2. Currently **NOT** support encrypt transfer (It only do turn by seq)

# Installation

## Client

### Windows

1. install [python 2.7](https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi)
2. install [Twisted](https://pypi.python.org/packages/2.7/T/Twisted/Twisted-14.0.2.win32-py2.7.msi) and [zope](https://pypi.python.org/packages/2.7/z/zope.interface/zope.interface-4.1.1.win32-py2.7.exe#md5=8b36e1fcd506ac9fb325ddf1c7238b07)

Note: suggest install [iocp support](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py2.7.exe/download)

### Linux
    
    pip install twisted

# Configuration

edit config.py

# Usage

Server:

    python server.py

Client:
   
    `python local.py`
 Or (for windows double click it)
 
# License

GPLv3

#敢不敢不把翻转传输给墙了，人在做天在看
