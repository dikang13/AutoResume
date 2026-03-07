"""User profile management for persistent memory across sessions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile containing experience, skills, and preferences."""

    user_id: str = Field(description="Unique identifier for the user")
    name: str = Field(default="", description="User's name")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    experiences: List[Dict[str, str]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[Dict[str, str]] = Field(default_factory=list)
    preferences: Dict[str, str] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    resume_files: List[str] = Field(default_factory=list)


class UserProfileManager:
    """Manages user profiles and persistent memory."""

    def __init__(self, profiles_dir: str = ".user_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)

    def _get_profile_path(self, user_id: str) -> Path:
        safe_id = user_id.replace("/", "_").replace("\\", "_")
        return self.profiles_dir / f"{safe_id}.json"

    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        profile_path = self._get_profile_path(user_id)
        if not profile_path.exists():
            return None
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserProfile(**data)
        except Exception:
            return None

    def save_profile(self, profile: UserProfile) -> None:
        profile.updated_at = datetime.now().isoformat()
        profile_path = self._get_profile_path(profile.user_id)
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, indent=2)

    def create_profile(self, user_id: str, name: str = "", resume_path: str = "") -> UserProfile:
        profile = UserProfile(
            user_id=user_id,
            name=name,
            resume_files=[resume_path] if resume_path else []
        )
        self.save_profile(profile)
        return profile

    def update_from_conversation(
        self,
        user_id: str,
        experiences: Optional[List[Dict[str, str]]] = None,
        skills: Optional[List[str]] = None,
        notes: Optional[List[str]] = None
    ) -> None:
        profile = self.load_profile(user_id)
        if profile is None:
            profile = self.create_profile(user_id)

        if experiences:
            for exp in experiences:
                if exp not in profile.experiences:
                    profile.experiences.append(exp)
        if skills:
            for skill in skills:
                if skill not in profile.skills:
                    profile.skills.append(skill)
        if notes:
            for note in notes:
                if note not in profile.notes:
                    profile.notes.append(note)

        self.save_profile(profile)

    def find_profile_by_resume(self, resume_path: str) -> Optional[UserProfile]:
        resume_path = str(Path(resume_path).resolve())
        for profile_file in self.profiles_dir.glob("*.json"):
            profile = self.load_profile(profile_file.stem)
            if profile:
                for saved_path in profile.resume_files:
                    if str(Path(saved_path).resolve()) == resume_path:
                        return profile
        return None
