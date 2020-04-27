#!/usr/bin/env python3

import  sys
import  os
from    optparse import OptionParser
import  shutil
import  getpass
import  site

class DebBuilderError(Exception):
    pass

class UIO(object):
    """@brief Responsible for user output"""
    def info(self, line):
        """@breif Show an info level message
           @param line The line of text."""
        print( 'INFO:  %s' % (line) )

    def error(self, line):
        """@breif Show an error level message
           @param line The line of text."""
        print( 'ERROR: %s' % (line) )


class DebBuilder(object):
    """@brief Responsible for building debian files using distutils and python-stdeb packages"""

    DEBIAN_FOLDER        = "debian"
    BUILD_FOLDER         = "build"
    INITD_FOLDER         = "init.d"
    ROOT_FS_FOLDER       = "root_fs"
    BUILD_DEBIAN_FOLDER  = "%s/DEBIAN" % (BUILD_FOLDER)
    BIN_FILES_FOLDER     = "%s/usr/local/bin" % (BUILD_FOLDER)
    DIST_INITD_FOLDER    = "%s/etc/init.d" % (BUILD_FOLDER)
    OUTPUT_FOLDER        = "packages"

    def __init__(self, uio, options):
        """@brief Constructor
           @param uio A UIO instance
           @param options The command line options instance"""

        self._uio = uio
        self._options = options

        self._pythonFiles = None
        self._debianFiles = None
        self._packageName = None
        self._version     = None

        self._sitePackagesFolder = "%s%s" % (DebBuilder.BUILD_FOLDER, site.getsitepackages()[0])

    def _getpythonFiles(self):
        """@brief Get the python files to install in site packages.
                  Python files should be placed in the python folder."""
        cwd = os.getcwd()
        pythonFolder = os.path.join(cwd, "python")
        entryList = os.listdir(pythonFolder)
        pythonFileList = []
        for entry in entryList:
            pythonFileList.append(os.path.join(pythonFolder, entry) )
        return pythonFileList

    def _getFileList(self, folder):
        """@brief Get the debian files."""
        fileList = []
        cwd = os.getcwd()
        folder = os.path.join(cwd, folder)

        if os.path.isdir(folder):
            entryList = os.listdir(folder)

            for entry in entryList:
                fileList.append(os.path.join(folder, entry) )

        return fileList

    def _clean(self, removeOutputFolder=False):
        """@brief Clean up files
           @param removePackagesFolder If True then remove the packages folder."""

        localDir = "build"
        if os.path.isdir(localDir):
            shutil.rmtree(localDir)
            self._uio.info("Removed %s path" % (localDir) )

        if os.path.isdir(DebBuilder.OUTPUT_FOLDER) and removeOutputFolder:
            shutil.rmtree(DebBuilder.OUTPUT_FOLDER)
            self._uio.info("Removed %s path" % (DebBuilder.OUTPUT_FOLDER) )

    def _loadPackageAttr(self):
        """@brief Get the name of the package to be built.
            _getDebianFiles() must have been called previously."""
        packageName=None
        for debianFile in self._debianFiles:
            if debianFile.endswith("control"):
                fd = open(debianFile)
                lines = fd.readlines()
                fd.close()
                for line in lines:
                    line=line.strip()
                    if line.startswith("Package: "):
                        packageName = line[8:]
                        self._packageName=packageName.strip()
                    if line.startswith("Version: "):
                        version = line[8:]
                        self._version=version.strip()

    def _loadFileLists(self):
        """@load local file lists."""

        reqFile = os.path.join(DebBuilder.DEBIAN_FOLDER, "control")
        if not os.path.isfile(reqFile):
            raise DebBuilderError("%s required file not found." % (reqFile) )

        self._pythonFiles = self._getpythonFiles()
        if len(self._pythonFiles) == 0:
            raise DebBuilderError("No python files found to install. These should be in the local python folder.")

        self._debianFiles = self._getFileList(DebBuilder.DEBIAN_FOLDER)

        self._initdFiles = self._getFileList(DebBuilder.INITD_FOLDER)

        self._rootFSFiles = self._getFileList(DebBuilder.ROOT_FS_FOLDER)

        self._loadPackageAttr()

    def _runLocalCmd(self, cmd):
        """@brief Run a command
           @param cmd The command to run"""
        self._uio.info("Running: %s" % (cmd) )
        rc = os.system(cmd)
        if rc != 0:
            raise DebBuilderError("!!! COMMAND FAILED !!!")

    def _copyFiles(self):
        """@Copy files into the local build area"""

        os.makedirs(DebBuilder.BUILD_DEBIAN_FOLDER)
        self._uio.info("Created %s" % (DebBuilder.BUILD_DEBIAN_FOLDER))

        if not os.path.isdir(self._sitePackagesFolder):
            os.makedirs(self._sitePackagesFolder)
            self._uio.info("Created %s" % (self._sitePackagesFolder))

        os.makedirs(DebBuilder.BIN_FILES_FOLDER)
        self._uio.info("Created %s" % (DebBuilder.BIN_FILES_FOLDER))

        os.makedirs(DebBuilder.DIST_INITD_FOLDER)
        self._uio.info("Created %s" % (DebBuilder.DIST_INITD_FOLDER))

        if not os.path.isdir(DebBuilder.OUTPUT_FOLDER):
            os.makedirs(DebBuilder.OUTPUT_FOLDER)
            self._uio.info("Created %s" % (DebBuilder.OUTPUT_FOLDER))

        for pythonFile in self._pythonFiles:
            if os.path.isfile(pythonFile):
                shutil.copy(pythonFile, self._sitePackagesFolder)
                self._uio.info("Copied %s to %s" % (pythonFile, self._sitePackagesFolder))
            else:
                destFolder = os.path.join(self._sitePackagesFolder, os.path.basename(pythonFile))
                shutil.copytree(pythonFile, destFolder)
                self._uio.info("Copied %s to %s" % (pythonFile, destFolder))

        for pythonFile in self._pythonFiles:
            filename = os.path.basename(pythonFile)
            if os.path.isfile(pythonFile) and pythonFile.endswith(".py"):
                filename = filename.replace(".py", "")
                destFile = os.path.join(DebBuilder.BIN_FILES_FOLDER, filename)
                fd = open(destFile, 'w')
                fd.write( "#!/usr/bin/env python3\n" )
                fd.write( "import %s\n" % (filename) )
                fd.write( "%s.main()\n" % (filename) )
                fd.close()
                self._uio.info("Created %s" % (destFile))

        for initdFile in self._initdFiles:
            shutil.copy(initdFile, DebBuilder.DIST_INITD_FOLDER)
            self._uio.info("Copied %s to %s" % (initdFile, DebBuilder.DIST_INITD_FOLDER))

        for rootFSFile in self._rootFSFiles:
            if os.path.isfile(rootFSFile):
                shutil.copy(rootFSFile, DebBuilder.BUILD_FOLDER)
                self._uio.info("Copied %s to %s" % (rootFSFile, DebBuilder.BUILD_FOLDER))
            else:
                destFolder = os.path.join(DebBuilder.BUILD_FOLDER, os.path.basename(rootFSFile))
                shutil.copytree(rootFSFile, destFolder)
                self._uio.info("Copied %s to %s" % (rootFSFile, destFolder))

        for debianFile in self._debianFiles:
            shutil.copy(debianFile, DebBuilder.BUILD_DEBIAN_FOLDER)
            self._uio.info("Copied %s to %s" % (debianFile, DebBuilder.BUILD_DEBIAN_FOLDER))

        #Enusre the file/dir attr are correct
        self._runLocalCmd("chmod 755 -R build")
        self._runLocalCmd("sudo chown -R root build")

        buildCmd = "dpkg-deb -Zgzip -b %s %s/%s-%s-all.deb" % (DebBuilder.BUILD_FOLDER, DebBuilder.OUTPUT_FOLDER, self._packageName, self._version)
        self._runLocalCmd(buildCmd)

        self._createPackagesFromDeb()

    def _createPackagesFromDeb(self):
        """@brief Create other packages from the deb file which must be built prior to calling this methid."""
        entryList = os.listdir(DebBuilder.OUTPUT_FOLDER)
        for entry in entryList:
            if entry.startswith(self._packageName) and entry.endswith(".deb") and entry.find(self._version) > 0:
                cwd = os.getcwd()
                os.chdir(DebBuilder.OUTPUT_FOLDER)
                if self._options.rpm:
                    buildCmd = "alien --to-rpm --scripts %s" % (entry)
                    self._runLocalCmd(buildCmd)
                    self._uio.info("Created rpm file from deb")

                if self._options.tgz:
                    buildCmd = "alien --to-tgz --scripts %s" % (entry)
                    self._runLocalCmd(buildCmd)
                    self._uio.info("Created tgz file from deb")
                os.chdir(cwd)

    def _build(self):
        """@brief Build the package"""

        self._copyFiles()

    def _ensureRootUser(self):
        """@brief Ensure this script is run as root """

        username = getpass.getuser()
        if username != 'root':
            raise DebBuilderError("Please run build.py as root using sudo.")

    def run(self):
        """@brief Run the build process."""

        self._ensureRootUser()

        if self._options.clean:

            self._clean(self._options.clean)

        else:

            self._loadFileLists()

            self._clean()

            self._build()

            if not self._options.lbp:
                self._clean()

def main():
    uio = UIO()

    opts = OptionParser(usage=  'usage: %prog [options]\n'
                                '\nBuild deb and rpm Linux install packages for a python program.\n\n'
                                'The following folders are required.\n'
                                'python:       Contains the python file/s and or folders to be installed.\n'
                                '              Any python files in here are converted to commands. The\n'
                                '              commands will be named the same as the python filename without\n'
                                '              the .py on the end. Each python file must contain a main() method.\n'
                                '              Any folders inside the python folder will be copied to the python\n'
                                '              dist packages path.\n'
                                'debian:       Contains the debian builder files as detailed below.\n'
                                '              control:  The debian config file.\n'
                                '              preinst:  Script executed before installation.\n'
                                '              postinst: Script executed after installation.\n'
                                '              prerm:    Script executed before removal.\n'
                                '              postrm:   Script executed after removal.\n\n'
                                'The following folders are optional.\n'
                                'root_fs:      Contains files to be copied into the root of the destination file system.\n'
                                'init.d:       Contains startup script file/s to be installed into /etc/init.d. Alternativley\n'
                                '              these files could be placed in the root_fs folder under /etc/init.d.\n\n'
                                'The output package (.deb and .rpm) files are placed in the local {} folder.\n'.format(DebBuilder.OUTPUT_FOLDER)
                        )
    opts.add_option("--debug", help="Enable debugging.", action="store_true", default=False)
    opts.add_option("--clean", help="Remove the %s folder." % (DebBuilder.OUTPUT_FOLDER), action="store_true", default=False)
    opts.add_option("--lbp",   help="Leave build path. A debugging option to allow the build folder to be examined after the build has completed.", action="store_true", default=False)
    opts.add_option("--rpm",   help="Generate an rpm output file as well as the deb file.", action="store_true", default=False)
    opts.add_option("--tgz",   help="Generate an tgz output file as well as the deb file.", action="store_true", default=False)

    try:
        (options, args) = opts.parse_args()

        debBuilder = DebBuilder(uio, options)
        debBuilder.run()

    # If the program throws a system exit exception
    except SystemExit:
        pass
    # Don't print error information if CTRL C pressed
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        if options.debug:
            raise

        else:
            uio.error(str(ex))

if __name__ == '__main__':
    main()
