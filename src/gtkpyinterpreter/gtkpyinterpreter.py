from code import InteractiveInterpreter
from gi.repository import Gtk
from gi.repository import GObject
import os
import sys


class GtkInterpreter(InteractiveInterpreter):
  
  def __init__(self, stdout, stderr, interpreter_locals):
    InteractiveInterpreter.__init__(self, interpreter_locals)
    self.stdout = stdout
    self.stderr = stderr
    
  def runcode(self, cmd):
    sys.stdout = self.stdout
    sys.stderr = self.stderr
    result = InteractiveInterpreter.runcode(self, cmd)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return result
    
  def write(self, data):
    if data.strip() != 'None':
      self.stderr.write(data)
    
    
class GtkInterpreterStandardOutput(object):
  
  __gproperties__ = {'auto-scroll': (GObject.TYPE_BOOLEAN, "auto-scroll",
                                    "Whether to automatically scroll the output.",
                                    True, GObject.PARAM_READWRITE)}
  
  def __init__(self, textview):
    super(GtkInterpreterStandardOutput, self).__init__()
    self.textview = textview
    #properties
    self._prop_auto_scroll = True
    
  def write(self, txt):
    textbuffer = self.textview.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, txt)
    if self._prop_auto_scroll:
      self.textview.scroll_mark_onscreen(textbuffer.get_insert())
    
  def get_property(self, prop):
    if prop.name == 'auto-scroll':
      return self._prop_auto_scroll
    else:
      return super(GtkPythonInterpreter, self).get_property(prop)
    
  def set_property(self, prop, val):
    if prop.name == 'auto-scroll':
      self._prop_auto_scroll = val
    else:
      super(GtkPythonInterpreter, self).set_property(prop, val)
      
  def get_auto_scroll(self):
    return self.get_property('auto-scroll')
      
  def set_auto_scroll(self, scroll):
    self.set_property('auto-scroll', scroll)
    
    
class GtkInterpreterErrorOutput(GtkInterpreterStandardOutput):
  
  def __init__(self, textview, color='#cc0000'):
    super(GtkInterpreterErrorOutput, self).__init__(textview)
    self.textview.get_buffer().create_tag(tag_name='error', foreground=color)
    
  def write(self, txt):
    textbuffer = self.textview.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert_with_tags_by_name(textiter, txt, 'error')
    if self._prop_auto_scroll:
      self.textview.scroll_mark_onscreen(textbuffer.get_insert())
    
    
class CommandHistory(object):
  
  def __init__(self, filename=None):
    super(CommandHistory, self).__init__()
    self._cmds = []
    self._idx = -1
    self._filename = filename
    self._load_from_file()
    
  #private methods
  def _load_from_file(self):
    if self._filename != None and os.path.exists(self._filename):
      f = open(self._filename, 'r')
      data = f.read()
      f.close()
      items = data.split('\n')
      items = filter(lambda x: x.strip != '', items)
      self._cmds = items
      self._idx = len(self._cmds) - 1
    
  def _add_to_file(self, cmd):
    if self._filename != None:
      f = open(self._filename, 'a')
      f.write(cmd + '\n')
      f.close()
      
  def _clear_file(self):
    if self._filename != None and os.path.exists(self._filename):
      f = open(self._filename, 'w')
      f.write('')
      f.close()
  
  #public methods
  def add(self, cmd):
    self._cmds.append(cmd)
    self._idx = len(self._cmds)
    self._add_to_file(cmd)
  
  def clear(self):
    self._cmds = []
    self._idx = -1
    self._clear_file()
    
  def down(self):
    if self._cmds == [] or self._idx >= len(self._cmds) - 1:
      return None
    else:
      self._idx += 1
      cmd = self._cmds[self._idx]
      return cmd
    
  def up(self):
    if self._cmds == [] or self._idx <= 0:
      return None
    else:
      self._idx -= 1
      cmd = self._cmds[self._idx]
      return cmd


class GtkPyInterpreterWidget(Gtk.VBox):
  
  __gproperties__ = {'auto-scroll': (GObject.TYPE_BOOLEAN, "auto-scroll",
                                    "Whether to automatically scroll the output.",
                                    True, GObject.PARAM_READWRITE)}
  
  name = '__console__'
  line_start = ' >>>'
  banner = 'Welcome to the GtkPyInterpreterWidget :-)'
  
  def __init__(self, interpreter_locals={}, history_fn=None):
    super(GtkPyInterpreterWidget, self).__init__()
    #properties
    self._prop_auto_scroll = True
    self._prev_cmd = []
    self._pause_interpret = False
    #history
    self._history = CommandHistory(history_fn)
    #output
    sw = Gtk.ScrolledWindow()
    self.output = Gtk.TextView()
    self.output.set_wrap_mode(Gtk.WrapMode.WORD)
    self.output.set_editable(False)
    self.output.set_left_margin(4)
    self.output.set_right_margin(4)
    sw.add(self.output)
    self.pack_start(sw, True, True, 0)
    #write banner to output
    textbuffer = self.output.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, self.banner + '\n\n')
    #input
    self.input = Gtk.Entry()
    self.pack_start(self.input, False, False, 0)
    self.input.connect('activate', self._cb_command_receive)
    self.input.connect('key-press-event', self._cb_input_key_press)
    #locals
    if not '__name__' in interpreter_locals:
      interpreter_locals['__name__'] = self.name
    if not '__doc__' in interpreter_locals:
      interpreter_locals['__doc__'] = self.__doc__
    if not '__class__' in interpreter_locals:
      interpreter_locals['__class__'] = self.__class__.__name__
    interpreter_locals['clear'] = self._clear
    #interpreter
    self.gtk_stdout = GtkInterpreterStandardOutput(self.output)
    self.gtk_stderr = GtkInterpreterErrorOutput(self.output)
    self.interpreter = GtkInterpreter(self.gtk_stdout, self.gtk_stderr, interpreter_locals)
    
  #callbacks    
  def _cb_command_receive(self, entry):
    """

    """
    #get command
    cmd = entry.get_text()
    entry.set_text('')
    #add to history
    self._history.add(cmd)
    #add output
    line_start = '' if self._prev_cmd != [] else self.line_start
    self.gtk_stdout.write('%s %s\n' % (line_start, cmd))
    #interpret command
    if not self._pause_interpret:
      res = self.interpreter.runsource(cmd)
      self.interpreter.showsyntaxerror()
    else:
      res = False
    if res == True:
      #wait for more input
      self.gtk_stdout.write('...')
      self._prev_cmd.append(cmd)
      self._pause_interpret = True
    else:
      if self._prev_cmd != [] and cmd.strip() == '':
        #compile multiline input
        self._prev_cmd.append(cmd)
        ncmd = '\n'.join(self._prev_cmd) + '\n'
        res = self.interpreter.runsource(ncmd)
        self._prev_cmd = []
        self._pause_interpret = False
      elif self._prev_cmd != []:
        self.gtk_stdout.write('...')
        self._prev_cmd.append(cmd)
      else:
        self._prev_cmd = []
    
  def _cb_input_key_press(self, entry, event):
    if event.keyval == 65362:
      #up
      cmd = self._history.up()
      if cmd != None:
        entry.set_text(cmd)
        entry.set_position(-1)
      return True
    elif event.keyval == 65364:
      #down
      cmd = self._history.down()
      if cmd != None:
        entry.set_text(cmd)
        entry.set_position(-1)
      else:
        entry.set_text('')
      return True
      
  #private methods    
  def _clear(self):
    self.output.get_buffer().set_text('')
      
  #gobject property methods
  def do_get_property(self, prop):
    if prop.name == 'auto-scroll':
      return self._prop_auto_scroll
    else:
      return super(GtkPythonInterpreter, self).get_property(prop)
    
  def do_set_property(self, prop, val):
    if prop.name == 'auto-scroll':
      self._prop_auto_scroll = val
      self._gtk_stdout.set_auto_scroll(val)
      self._gtk_stderr.set_auto_scroll(val)
    else:
      super(GtkPythonInterpreter, self).set_property(prop, val)
      
  #public methods
  def write(self, txt):
    textbuffer = self.output.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, txt)
      
  def get_auto_scroll(self):
    return self.get_property('auto-scroll')
      
  def set_auto_scroll(self, scroll):
    self.set_property('auto-scroll', scroll)
    
  def get_output_buffer(self):
    return self.output.get_buffer()
    
  def get_history(self):
    return self._history
      
      
if __name__ == '__main__':
  w = Gtk.Window()
  w.set_title('Gtk3 Interactive Python Interpreter')
  w.set_default_size(800, 600)
  w.connect('destroy', Gtk.main_quit)
  c = GtkPyInterpreterWidget({'window':w}, '/home/sven/temp/pyrc')
  w.add(c)
  w.show_all()
  Gtk.main()
