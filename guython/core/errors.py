class GuythonError(Exception): pass
class GuythonSyntaxError(GuythonError): pass
class GuythonRuntimeError(GuythonError): pass
class GuythonSecurityError(GuythonError): pass
class GuythonGotoException(Exception):
    def __init__(self, target_line: int):
        self.target_line = target_line
        super().__init__(f"Goto line {target_line}")
