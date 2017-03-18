from __future__ import absolute_import

from ipykernel.kernelapp import IPKernelApp
from traitlets import Dict

# -----------------------------------------------------------------------

class SpringRTSApp(IPKernelApp):
    """
    The main kernel application, inheriting from the ipykernel
    """
    from .kernel import SpringRTSKernel
    from .install import SpringRTSInstall, SpringRTSRemove
    kernel_class = SpringRTSKernel

    # We override subcommands to add our own install command
    subcommands = Dict({
        'install': (SpringRTSInstall,
                    SpringRTSInstall.description.splitlines()[0]),
        'remove': (SpringRTSRemove,
                   SpringRTSRemove.description.splitlines()[0]),
    })


# -----------------------------------------------------------------------

def main():
    """
    This is the installed entry point
    """
    SpringRTSApp.launch_instance()

if __name__ == '__main__':
    main()
