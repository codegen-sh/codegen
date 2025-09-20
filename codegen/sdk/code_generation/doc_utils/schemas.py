from typing import Literal

from pydantic import BaseModel
from pydantic.fields import Field


class ParameterDoc(BaseModel):
    name: str = Field(..., description="The name of the parameter")
    description: str = Field(..., description="The description of the parameter")
    type: str = Field(..., description="The type of the parameter")
    default: str = Field(default="", description="The default value of the parameter")


class MethodDoc(BaseModel):
    name: str = Field(..., description="The name of the method")
    description: str | None = Field(..., description="The description of the method")
    parameters: list[ParameterDoc] = Field(..., description="The parameters of the method")
    return_type: list[str] | None = Field(default=None, description="The return types of the method")
    return_description: str | None = Field(default=None, description="The return description of the method")
    method_type: Literal["method", "property", "attribute"] = Field(..., description="The type of the method")
    code: str = Field(..., description="The signature of the method or attribute")
    path: str = Field(..., description="The path of the method that indicates its parent class <language>/<class_name>/<method_name>")
    raises: list[dict] | None = Field(..., description="The raises of the method")
    metainfo: dict = Field(..., description="Information about the method's true parent class and path")
    version: str = Field(..., description="The commit hash of the git commit that generated the docs")
    github_url: str = Field(..., description="The github url of the method")


class ClassDoc(BaseModel):
    title: str = Field(..., description="The title of the class")
    description: str = Field(..., description="The description of the class")
    content: str = Field(..., description="The content of the class")
    path: str = Field(..., description="The path of the class")
    inherits_from: list[str] = Field(..., description="The classes that the class inherits from")
    version: str = Field(..., description="The commit hash of the git commit that generated the docs")
    methods: list[MethodDoc] = Field(default=[], description="The methods of the class")
    attributes: list[MethodDoc] = Field(default=[], description="The attributes of the class")
    github_url: str = Field(..., description="The github url of the class")


class GSDocs(BaseModel):
    classes: list[ClassDoc] = Field(..., description="The classes to document")
