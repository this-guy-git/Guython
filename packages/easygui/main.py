import easygui as gui

def App(name):
    global var
    var = gui.App(name)
    return "Started EasyGUI app with name ", name

def text(text):
    var.text(text)
    return "Added text ", text

def run():
    var.run()
    return "Running"