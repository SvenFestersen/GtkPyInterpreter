from code import InteractiveInterpreter
from gi.repository import Gdk
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
  
  def __init__(self, textview, eh_changed):
    super(GtkInterpreterStandardOutput, self).__init__()
    self.textview = textview
    #properties
    textbuffer = self.textview.get_buffer()
    textbuffer.create_tag(tag_name='protected', editable=False)
    self._input_mark = textbuffer.get_mark('input_start')
    self._prop_auto_scroll = True
    self._eh_changed = eh_changed
    
  def write(self, txt, move_cursor=False, tag_names=['protected']):
    textbuffer = self.textview.get_buffer()    
    textbuffer.handler_block(self._eh_changed)
    textiter = textbuffer.get_end_iter()
    textbuffer.insert_with_tags_by_name(textiter, txt, *tag_names)
    if self._prop_auto_scroll:
      self.textview.scroll_mark_onscreen(textbuffer.get_insert())
    textbuffer.move_mark(self._input_mark, textbuffer.get_end_iter())
    if move_cursor:
      textbuffer.place_cursor(textbuffer.get_iter_at_mark(self._input_mark))
    textbuffer.handler_unblock(self._eh_changed)
    
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
  
  def __init__(self, textview, eh_changed, color='#cc0000'):
    super(GtkInterpreterErrorOutput, self).__init__(textview, eh_changed)
    self.textview.get_buffer().create_tag(tag_name='error', foreground=color)
    
  def write(self, txt, move_cursor=False, tag_names=['protected', 'error']):
    super(GtkInterpreterErrorOutput, self).write(txt, move_cursor, tag_names)
    
    
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
    cmd = cmd.strip()
    if cmd == '': return
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
  line_start = ' >>> '
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
    textbuffer = self.output.get_buffer()
    self._input_mark = textbuffer.create_mark('input_start', textbuffer.get_start_iter(), True)
    sw.add(self.output)
    self.pack_start(sw, True, True, 0)
    self.eh_changed = textbuffer.connect('changed', self._cb_text_changed)
    self.output.connect('event', self._cb_textview_event)
    #locals
    if not '__name__' in interpreter_locals:
      interpreter_locals['__name__'] = self.name
    if not '__doc__' in interpreter_locals:
      interpreter_locals['__doc__'] = self.__doc__
    if not '__class__' in interpreter_locals:
      interpreter_locals['__class__'] = self.__class__.__name__
    interpreter_locals['clear'] = self._clear
    #interpreter
    self.gtk_stdout = GtkInterpreterStandardOutput(self.output, self.eh_changed)
    self.gtk_stderr = GtkInterpreterErrorOutput(self.output, self.eh_changed)
    self.interpreter = GtkInterpreter(self.gtk_stdout, self.gtk_stderr, interpreter_locals)
    #write banner to output
    self.gtk_stdout.write(self.banner + '\n\n' + self.line_start)
    
  #callbacks      
  def _cb_text_changed(self, textbuffer):
    start_iter = textbuffer.get_iter_at_mark(self._input_mark)
    end_iter = textbuffer.get_end_iter()
    txt = textbuffer.get_text(start_iter, end_iter, True)
    last_char = txt[-1]
    if last_char == '\n':
      textbuffer.apply_tag_by_name('protected', start_iter, end_iter)
      self._cmd_receive(txt[:-1])
      
  def _cb_textview_event(self, textview, event):
    if event.type == Gdk.EventType.KEY_PRESS:
      textbuffer = textview.get_buffer()
      if event.keyval == 65362:
        #up
        cmd = self._history.up()
        if cmd != None:
          start_iter = textbuffer.get_iter_at_mark(self._input_mark)
          end_iter = textbuffer.get_end_iter()
          textbuffer.handler_block(self.eh_changed)
          textbuffer.delete(start_iter, end_iter)
          start_iter = textbuffer.get_iter_at_mark(self._input_mark)
          textbuffer.insert(start_iter, cmd)
          textbuffer.handler_unblock(self.eh_changed)
        return True
      elif event.keyval == 65364:
        #down
        cmd = self._history.down()
        if cmd != None:
          start_iter = textbuffer.get_iter_at_mark(self._input_mark)
          end_iter = textbuffer.get_end_iter()
          textbuffer.handler_block(self.eh_changed)
          textbuffer.delete(start_iter, end_iter)
          start_iter = textbuffer.get_iter_at_mark(self._input_mark)
          textbuffer.insert(start_iter, cmd)
          textbuffer.handler_unblock(self.eh_changed)
        else:
          textbuffer.handler_block(self.eh_changed)
          start_iter = textbuffer.get_iter_at_mark(self._input_mark)
          end_iter = textbuffer.get_end_iter()
          textbuffer.delete(start_iter, end_iter)
          textbuffer.handler_unblock(self.eh_changed)
        return True
      
  #private methods    
  def _clear(self):
    self.output.get_buffer().set_text(self.line_start)
    
  def _cmd_receive(self, cmd):
    #add to history
    self._history.add(cmd)
    #add output
    line_start = '' if self._prev_cmd != [] else self.line_start
    #interpret command
    if not self._pause_interpret:
      res = self.interpreter.runsource(cmd)
      self.interpreter.showsyntaxerror()
    else:
      res = False
    if res == True:
      #wait for more input
      self.gtk_stdout.write('...', True)
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
        self.gtk_stdout.write(line_start, True)
      
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
