from gi.repository import Gtk
from gtkpyinterpreter.gtkpyinterpreter import GtkPyInterpreterWidget


if __name__ == '__main__':
  w = Gtk.Window()
  w.set_title('Gtk3 Interactive Python Interpreter')
  w.set_default_size(800, 600)
  w.connect('destroy', Gtk.main_quit)
  c = GtkPyInterpreterWidget({'window':w}, '/tmp/pyrc')
  c.set_font('LiberationMono 10')  
  w.add(c)
  w.show_all()
  Gtk.main()
