class Tool:
    
    def __init__(self, name: str, description:str, required_args:bool = True):
        self.name = name
        self.description = description
        self.required_args = required_args
        
    
    