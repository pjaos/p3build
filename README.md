# pbuild
The objective of pbuild was to provide a simple was of packaging python packages for installation onto a Debian Linux system.

# Installation
To install the pbuild package use the following commands once the git repo has been cloned onto the machine it is to be installed on.

```sudo ./pbuild.py
     sudo dpkg -i packages/python-pbuild-1.6-all.deb```

Alternatively you can use the following command if you wish to install via pip

```sudo pip install .```

# Usage
To generate a debian installer file the project folder must contain the following.

## python folder
This folder contains python files. python files sitting in this folder will become command line programs (minus the .py suffix) once installed on the target system. Folders inside the python folder will become python modules on the once installed on the target system. These will be install into the dist-packages folder on the target system.

A requirement for the python files sitting in the python folder (top level only) is that they have a main() method. Therefore the programs in this folder will typically have the following 

```
def main():
   ...

if __name__ == '__main__':
    main()
  
```

## debian
This folder holds the debian build control files. These are

### control
This file holds the main details of the package to be installed . This file must be present. The typical contents of this file is shown below.

```
Package: python-yourpackagename
Section: Network
Priority: optional
Architecture: all
Essential: no
Installed-Size: 25
Maintainer: yourname <your email address>
Description: A Description of the program function.
Version: 1.0
```

A comprehensive guide to the contents of the control file can be found at 
[https://www.debian.org/doc/debian-policy/ch-controlfields.html](https://www.debian.org/doc/debian-policy/ch-controlfields.html)

The other files that can be placed in this folder are
- postinst
A script file executed after the installation has completed. This file is optional.
- postrm
A script file executed after the installation has been removed. This file is optional.
- preinst
A script file executed befre the installation starts. This file is optional.
- prerm
A script file executed before an installation is removed. This file is optional.

## init.d folder
You can place you start-up scripts in here. These will be copied to /etc/init.d on the target system. This folder maybe omitted if no startup scripts are required for your application.

# Building a python package
- Edit the debian/control file and set the package name and version as a minimum.
- Run the following command in the folder that holds the python and debian folders

```sudo pbuild```

This will create a packages folder that will contain the python-*.deb install package.