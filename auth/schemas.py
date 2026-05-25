from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    

class UserLogin(BaseModel):
    identifier:Optional[str]=None
    email: Optional[str] =None
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class ChangePassword(BaseModel):
    old_password:str
    new_password:str

class UserUpdate(BaseModel):
    userName:Optional[str]=None
    userBio: Optional[List[str]]=None
    tagline:Optional[str]=None
    homeTown:Optional[str]=None
    avatarPath:Optional[str]=None


