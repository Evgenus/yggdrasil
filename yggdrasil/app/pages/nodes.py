from . import Page

class Nodes(Page):
    def __init__(self, runtime):
        pass

    def on_by_uid(self, request, uid): 
        return {"uid": uid}
