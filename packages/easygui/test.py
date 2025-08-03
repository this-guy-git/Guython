import easygui as gui

app = gui.App("My App")
app.text("Hello World!")
app.button("Click me!", lambda: print("Clicked!"))
app.run()