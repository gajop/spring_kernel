from ipykernel.kernelbase import Kernel

import base64
import os
import logging

from .utils import data_msg
from .spring_connector import SpringConnector

# The list of implemented magics with their help, as a pair [param,help-text]
magics = {
    '%lsmagics' : [ '', 'list all magics'],
    '%help' : [ '', 'show general help' ],
    '%show' : [ '', 'show the current screen' ],
    '%luaui' : [ 'LuaUI', 'execute code in LuaMenu/LuaUI state, whichever is present.'],
    '%luamenu' : [ 'LuaMenu', 'execute code in LuaMenu/LuaUI state, whichever is present.'],
    '%uluarules' : [ 'LuaRules Unsynced', 'execute code in unsynced LuaRules state'],
    '%sluarules' : [ 'LuaRules Synced', 'execute code in synced LuaRules state'],
    '_p' : [ '', 'Lua helper function to print data to the notebook'],
    '_s' : [ '', 'Lua helper function to print the function source code'],
}


# The full list of all magics
magic_help = ('Available magics:\n' +
              '  '.join( sorted(magics.keys()) ) +
              '\n\n' +
              '\n'.join( ('{0} {1} : {2}'.format(k,*magics[k])
                          for k in sorted(magics) ) ) )

general_help = """SpringRTS Lua notebook
To begin, write %lsmagic to see what special identifiers are available. Each code block should begin with a state identifier magic, such as: %luaui, %uluarules, and similar. This defines the Spring Lua state in which the code will be executed.

Additional things to note:
- In case there is no state magic in the code block, the last set state will be used.
- There can only be one state-magic per code block, and it must be at the beginning of the code block.
- Non-state magics such as %lsmagic, %help and similar shouldn't appear along with Lua code.
- Don't use local variables if you want to access them in consequitive runs. They will be out of scope.
- Variable scope is shared between different notebooks.
"""


class SpringRTSKernel(Kernel):
    implementation = 'SpringRTS'
    implementation_version = '1.0'
    language = 'lua'
    language_version = '0.1'
    language_info = {
        'name': 'Lua',
        'mimetype': 'text/plain',
        'file_extension': '.lua',
    }
    banner = "SpringRTS kernel - experimentation made easy"


    def maybe_magic(self, code):
        """
        Process code and execute magic. If code should still be executed afterwards, return it.
          @param code (string): code that might contain magic
        Magic is only recognized in the first (non-whitespace) line.
        State-magic like %luaui can exist with code
        """
        lines = code.splitlines()
        magic = None
        for i, line in enumerate(lines):
            line = line.strip()
            if line != "":
                if line[0] == '%':
                    magic = line[1:].lower()
                    indx = i
                break
        # Magic wasn't found in the first non-whitespace line
        if not magic:
            return

        # Remove magic from code but replace it with an empty line so line numbers make sense
        lines[indx] = ''
        code = '\n'.join(lines)

        if magic in ('?','help'):
            return {
                'output' : general_help,
                'outputType' : 'help'
            }
        elif magic == 'lsmagic':
            return {
                'output' : magic_help,
                'outputType' : 'help'
            }
        elif magic == 'show':
            return {
                'show' : True # uglish
            }
        elif magic in ["luaui", "uluarules", "sluarules", "luamenu"]:
            self.state = magic
            return {
                'code' : code,
            }
        else:
            return {
                'output' : "No such magic: %" + magic,
                'outputType' : 'error'
            }

    def __init__(self, *args, **kwargs):
        """
        Initialize the object
        """
        # Define logging status before calling parent constructor
        logging.basicConfig(filename='kernlog.log',level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting SpringRTS Kernel")

        self.state = "luaui"

        # Start base kernel
        super(SpringRTSKernel, self).__init__(*args, **kwargs)

        # Start Spring connector
        self.sc = SpringConnector()
        self.sc.start()

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        result = self.maybe_magic(code)
        if result is not None:
            if result.get('output'):
                return self._send(
                    data=[(result['output'], result.get('outputType'))],
                    status=result.get('outputType'))
            elif result.get('show'):
                self.logger.info("Asking to show screen")
                msg = {'command' : 'show'}
                results = self.sc.executeLua(msg) #results are ignored
                self.send_response(
                    self.iopub_socket,
                    'display_data', {
                        'data' : {
                            "image/png" : base64.b64encode(open(results["imgPath"], "rb").read()),
                        }
                    }
                )
                return {'status': 'ok',
                        # The base class increments the execution count
                        'execution_count': self.execution_count,
                        'payload': [],
                        'user_expressions': {},
                       }
                #return self._send(
                #    data=results,
                #    status='ok')
            elif result.get('code') is None:
                raise
            code = result['code']

        exec_state = magics["%" + self.state][0]
        msg = {
            'command' : 'execute',
            'data' : {
                'code' : code,
                'state' : self.state,
            },
        }
        self.logger.info("Got Lua to execute: {}".format(code))
        try:
            results = self.sc.executeLua(msg)
            self.logger.info("Got results: {}".format(results))
            data = [(exec_state, 'state-info')]
            data.extend(results)
            self.logger.info("Got results: {}".format(data))
            return self._send(
                data=data,
                status='ok')
        except Exception as ex:
            template = "Exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            self.logger.warning("message")
            return self._send(
                data=[("Timeout executing task", 'warning')],
                status='error')

        if not silent:
            stream_content = {'name': 'stdout', 'text': "user_expressions: {}".format(user_expressions)}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    def _send(self, data, status='ok', silent=False):
        """
        Send a response to the frontend and return an execute message
        """
        # Data to send back
        if data is not None and not silent:
            # Format the data
            data = data_msg(data)
            # Send the data to the frontend
            self.send_response(self.iopub_socket, 'display_data', data)

        # Result message
        return {'status': 'error' if status == 'error' else 'ok',
                # The base class will increment the execution count
                'execution_count': self.execution_count,
                'payload' : [],
                'user_expressions': {},
               }


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=SpringRTSKernel)
