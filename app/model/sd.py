from typing import Dict, List

from pydantic import BaseModel

# class syntax



class Response(BaseModel):
    targets: List[str]
    labels: Dict[str, str]
