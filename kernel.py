from ipykernel.kernelbase import Kernel
import logging
from utils import KrnlException, data_msg


# The list of implemented magics with their help, as a pair [param,help-text]
magics = {
    '%lsmagics' : [ '', 'list all magics'],
    '%help' : [ '', 'show general help' ],
    '%synced' : [ '', 'execute code in synced LuaRules state'],
    '%unsynced' : [ '', 'execute code in unsynced LuaRules state'],
    '%widget' : [ '', 'execute code in LuaUI state'],
    '%menu' : [ '', 'execute code in LuaMenu state'],
}


# The full list of all magics
magic_help = ('Available magics:\n' +
              '  '.join( sorted(magics.keys()) ) +
              '\n\n' +
              '\n'.join( ('{0} {1} : {2}'.format(k,*magics[k])
                          for k in sorted(magics) ) ) )

# The generic help message TODO
general_help = """SpringRTS Lua notebook
You can start by loading a database of rules:
%learn alice | standard | <dbdirectory> | <xml-file>
For "alice" & "standard" databases, the rules will
automatically be activated. For a custom database,
you will need to launch the "load <name>" command
defined in it.
Once loaded, you can start chatting with the bot.
New databases can be added by additional "%learn" commands.
Use "%lsmagic" to see all the available magics.
"""

# Utils from https://github.com/paulovn/aiml-chatbot-kernel/blob/master/aimlbotkernel/kernel.py

def split_magics( buffer ):
    """
    Split the cell by lines and decide if it contains magic or bot input
      @return (tuple): a pair \c stripped_lines,is_magic
    """
    # Split by lines, strip whitespace & remove comments. Keep empty lines
    buffer_lines = [ ls for ls in ( l.strip() for l in buffer.split('\n') )
                     if not ls or ls[0] !='#' ]

    # Remove leading empty lines
    i = 0
    for i, line in enumerate(buffer_lines):
        if line:
            break
    if i>0:
        buffer_lines = buffer_lines[i:]

    # Decide if magic or not & return
    if not buffer_lines:
        return None, None
    elif buffer_lines[0][0] == '%':
        return buffer_lines, True
    else:
        return u'\n'.join(buffer_lines), False


def is_magic( token, token_start, buf ):
    """
    Detect if the passed token corresponds to a magic command: starts
    with a percent, and it's at the beginning of the buffer
    """
    return token[0] == '%' and token_start==0

def token_at_cursor( code, pos=0 ):
    """
    Find the token present at the passed position in the code buffer
    """
    l = len(code)
    end = start = pos
    # Go forwards while we get alphanumeric chars
    while end<l and code[end].isalpha():
        end+=1
    # Go backwards while we get alphanumeric chars
    while start>0 and code[start-1].isalpha():
        start-=1
    # If previous character is a %, add it (potential magic)
    if start>0 and code[start-1] == '%':
        start -= 1
    return code[start:end], start

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
    banner = "SpringRTS kernel - remote execution made easy"


    def magic(self, lines):
        """
        Process magic cells
          @param lines (list): list of lines containing magics
        For most of the magics only one magic line is recognized. The
        exceptions are %aiml (which uses the whole cell) and %setp (which
        can appear multiple times in a cell).
        """
        kw = lines[0].split()
        magic = kw[0][1:].lower()

        if magic in ('?','help'):
            return general_help, 'help'
        elif magic.startswith('lsmagic'):
            return magic_help, 'help'
        elif magic == "synced":
            state = 1
            return str(state), "Lua state is " + str(state)
        elif magic == "unsynced":
            state = 2
            return str(state), "Lua state is " + str(state)
        elif magic == "widget":
            state = 3
            return str(state), "Lua state is " + str(state)
        elif magic == "menu":
            state = 4
            return str(state), "Lua state is " + str(state)
        else:
            raise KrnlException( 'unknown magic: {}', magic )

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):

        content, is_magic = split_magics(code)
        if is_magic :
            return self._send(*self.magic(content))

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
            data = data_msg( data, mtype=status )
            # Send the data to the frontend
            self.send_response( self.iopub_socket, 'display_data', data )

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
