from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(description="Uploaded file name on the server")
    file_type: str = Field(description="Type of file: video or illumination")
    size_bytes: int = Field(ge=0, description="Size of the uploaded file in bytes")
    message: str = Field(default="File uploaded successfully", description="Status message")

