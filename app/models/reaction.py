from sqlmodel import Field, SQLModel
import uuid


class Reaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: uuid.UUID = Field(foreign_key="post.id")
    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    reaction_type: str


class ReactionCreate(SQLModel):
    post_id: uuid.UUID
    profile_id: uuid.UUID
    reaction_type: str


class ReactionPublic(SQLModel):
    id: uuid.UUID
    post_id: uuid.UUID
    profile_id: uuid.UUID
    reaction_type: str
