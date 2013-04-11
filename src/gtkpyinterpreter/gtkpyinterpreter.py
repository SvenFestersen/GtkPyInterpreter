from code import InteractiveInterpreter
from gi.repository import Gtk
from gi.repository import GObject
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
    
    
class GtkInterpreterStandardOutput(object):
  
  def __init__(self, textview):
    super(GtkInterpreterStandardOutput, self).__init__()
    self.textview = textview
    
  def write(self, txt):
    textbuffer = self.textview.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, txt)
    
    
class GtkInterpreterErrorOutput(GtkInterpreterStandardOutput):
  
  def __init__(self, textview, color='#cc0000'):
    super(GtkInterpreterErrorOutput, self).__init__(textview)
    self.textview.get_buffer().create_tag(tag_name='error', foreground=color)
    
  def write(self, txt):
    textbuffer = self.textview.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert_with_tags_by_name(textiter, txt, 'error')
    
    
class CommandHistory(object):
  
  def __init__(self):
    super(CommandHistory, self).__init__()
    self._cmds = []
    self._idx = -1
    
  def add(self, cmd):
    self._cmds.append(cmd)
    self._idx = len(self._cmds)
    
  def up(self):
    if self._cmds == [] or self._idx <= 0:
      return None
    else:
      self._idx -= 1
      cmd = self._cmds[self._idx]
      return cmd
      
  def down(self):
    if self._cmds == [] or self._idx >= len(self._cmds) - 1:
      return None
    else:
      self._idx += 1
      cmd = self._cmds[self._idx]
      return cmd


class GtkPyInterpreterWidget(Gtk.VBox):
  
  __gproperties__ = {'auto-scroll': (GObject.TYPE_BOOLEAN, "auto-scroll",
                                    "Whether to automatically scroll the output.",
                                    True, GObject.PARAM_READWRITE)}
  
  name = '__console__'
  line_start = ' >>>'
  
  def __init__(self, interpreter_locals={}):
    super(GtkPyInterpreterWidget, self).__init__()
    #properties
    self._prop_auto_scroll = True
    #locals
    if not '__name__' in interpreter_locals:
      interpreter_locals['__name__'] = self.name
    if not '__doc__' in interpreter_locals:
      interpreter_locals['__doc__'] = self.__doc__
    if not '__class__' in interpreter_locals:
      interpreter_locals['__class__'] = self.__class__.__name__
    #history
    self._history = CommandHistory()
    #output
    sw = Gtk.ScrolledWindow()
    self.output = Gtk.TextView()
    self.output.set_editable(False)
    self.output.get_buffer().connect_after('changed', self._cb_output_buffer_insert)
    sw.add(self.output)
    self.pack_start(sw, True, True, 0)
    #input
    self.input = Gtk.Entry()
    self.pack_start(self.input, False, False, 0)
    self.input.connect('activate', self._cb_command_receive)
    self.input.connect('key-press-event', self._cb_input_key_press)
    #interpreter
    self.gtk_stdout = GtkInterpreterStandardOutput(self.output)
    self.gtk_stderr = GtkInterpreterErrorOutput(self.output)
    self.interpreter = GtkInterpreter(self.gtk_stdout, self.gtk_stderr, interpreter_locals)
    
  #callbacks    
  def _cb_command_receive(self, entry):
    """
    TODO: fix multiline input
    """
    #get command
    cmd = entry.get_text()
    entry.set_text('')
    #add to history
    self._history.add(cmd)
    #add output
    textbuffer = self.output.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, '%s %s\n' % (self.line_start, cmd))
    #interpret command
    res = self.interpreter.runsource(cmd)
    print res
    if res == True:
      #wait for more input
      textiter = textbuffer.get_end_iter()
      textbuffer.insert(textiter, ' ...')
    elif res == False:
      #exception
      pass
    else:
      #result
    
  def _cb_input_key_press(self, entry, event):
    if event.keyval == 65362:
      #up
      cmd = self._history.up()
      if cmd != None:
        entry.set_text(cmd)
      return True
    elif event.keyval == 65364:
      #down
      cmd = self._history.down()
      if cmd != None:
        entry.set_text(cmd)
      else:
        entry.set_text('')
      return True
      
  def _cb_output_buffer_insert(self, textbuffer):
    if self._prop_auto_scroll:
      self.output.scroll_to_iter(textbuffer.get_end_iter(), 0.0, False, 0.5, 0.5)
      
  #public methods
  def write(self, txt):
    textbuffer = self.output.get_buffer()    
    textiter = textbuffer.get_end_iter()
    textbuffer.insert(textiter, txt)
    
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
      
      
if __name__ == '__main__':
  w = Gtk.Window()
  w.set_default_size(800, 600)
  w.connect('destroy', Gtk.main_quit)
  c = GtkPyInterpreterWidget({'window':w})
  w.add(c)
  w.show_all()
  Gtk.main()
