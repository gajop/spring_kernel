"""
Perform kernel installation, including
  * json kernel specfile
  * kernel resources (logo images)
"""

from __future__ import print_function
import sys
import os
import os.path
import json
import pkgutil
import io

from jupyter_client.kernelspecapp  import InstallKernelSpec, RemoveKernelSpec
from traitlets import Unicode

from IPython.utils.path import ensure_dir_exists
from IPython.utils.tempdir import TemporaryDirectory

from . import __version__, KERNEL_NAME, DISPLAY_NAME

PY3 = sys.version_info[0] == 3
if PY3:
    unicode = str

MODULEDIR = os.path.dirname(__file__)
PKGNAME = os.path.basename(MODULEDIR)


# The kernel specfile
kernel_json = {
    "argv": [sys.executable,
	     "-m", PKGNAME,
	     "-f", "{connection_file}"],
    "display_name": DISPLAY_NAME,
    "name": KERNEL_NAME
}


# --------------------------------------------------------------------------


def copyresource(resource, filename, destdir):
    """
    Copy a resource file to a destination
    """
    data = pkgutil.get_data(resource, os.path.join('resources',filename) )
    #log.info( "Installing %s", os.path.join(destdir,filename) )
    with io.open(os.path.join(destdir,filename), 'wb' ) as fp:
        fp.write( data )


def install_kernel_resources(destdir, resource=PKGNAME, files=None):
    """
    Copy the resource files to the kernelspec folder.
    """
    if files is None:
        files = ['logo-64x64.png', 'logo-32x32.png']
    for filename in files:
        try:
            copyresource(resource, filename, destdir)
        except Exception as e:
            sys.stderr.write(str(e))


# --------------------------------------------------------------------------


class SpringRTSInstall(InstallKernelSpec):
    """
    The kernel installation class
    """

    version = __version__
    kernel_name = KERNEL_NAME
    description = '''Install the SpringRTS Kernel
    Either as a system kernel or for a concrete user'''

    logdir = Unicode(os.environ.get('LOGDIR', ''),
        config=True,
        help="""Default directory to use for the logfile."""
    )
    aliases =  { 'logdir' : 'SpringRTSInstall.logdir' }

    def parse_command_line(self, argv):
        """
        Skip parent method and go for its ancestor
        (because parent method requires an extra argument: the kernel to install)
        """
        super(InstallKernelSpec, self).parse_command_line(argv)


    def start(self):
        if self.user and self.prefix:
            self.exit("Can't specify both user and prefix. Please choose one or\
 the other.")

        self.log.info('Installing SpringRTS kernel')
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755) # Starts off as 700, not user readable
            # Add kernel spec
            if len(self.logdir):
                kernel_json['env'] = { 'LOGDIR_DEFAULT' : self.logdir }
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            # Add resources
            install_kernel_resources(td, resource=PKGNAME)
            # Install JSON kernel specification + resources
            self.log.info('Installing kernel spec')
            self.sourcedir = td
            install_dir = self.kernel_spec_manager.install_kernel_spec( td,
                kernel_name=self.kernel_name,
                user=self.user,
                prefix=self.prefix,
                replace=self.replace,
            )
        self.log.info("Installed into %s", install_dir)

# --------------------------------------------------------------------------


class SpringRTSRemove(RemoveKernelSpec):
    """
    The kernel uninstallation class
    """

    spec_names = [KERNEL_NAME]
    description = '''Remove the SpringRTS Kernel'''

    def parse_command_line(self, argv):
        """
        Skip parent method and go for its ancestor
        (because parent method requires an extra argument: the kernel to remove)
        """
        super(RemoveKernelSpec, self).parse_command_line(argv)

    def start(self):
        # Call parent (this time the real parent) to remove the kernelspec dir
        super(SpringRTSRemove, self).start()
